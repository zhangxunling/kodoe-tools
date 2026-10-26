#!/usr/bin/env python3
"""Ecloud 集群导航的受认证本地服务。"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import sqlite3
import ssl
import sys
import threading
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR / "ecloud-data.sqlite3"
SESSION_COOKIE = "ecloud_session"
SESSION_TTL = timedelta(hours=12)
PBKDF2_ITERATIONS = 600_000
MAX_BODY_BYTES = 1_000_000
CLUSTER_FIELDS = ("region", "name", "clusterId", "url", "username", "password", "note")


class App:
    def __init__(self, database_path: Path, password: str) -> None:
        self.database_path = database_path
        self.password = password.encode("utf-8")
        self.sessions: dict[str, datetime] = {}
        self.lock = threading.Lock()
        self.setup_database()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def setup_database(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS clusters (
                    id TEXT PRIMARY KEY,
                    region TEXT NOT NULL,
                    name TEXT NOT NULL,
                    cluster_id TEXT NOT NULL DEFAULT '',
                    url TEXT NOT NULL,
                    username TEXT NOT NULL DEFAULT '',
                    password TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )

    def verify_password(self, password: str) -> bool:
        return hmac.compare_digest(self.password, password.encode("utf-8"))

    def create_session(self) -> str:
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.sessions[token] = datetime.now(timezone.utc) + SESSION_TTL
        return token

    def is_authenticated(self, token: str | None) -> bool:
        if not token:
            return False
        with self.lock:
            expires_at = self.sessions.get(token)
            if not expires_at or expires_at <= datetime.now(timezone.utc):
                self.sessions.pop(token, None)
                return False
            return True

    def remove_session(self, token: str | None) -> None:
        if token:
            with self.lock:
                self.sessions.pop(token, None)

    def list_clusters(self) -> list[dict[str, str]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, region, name, cluster_id, url, username, password, note FROM clusters ORDER BY region COLLATE NOCASE, name COLLATE NOCASE"
            ).fetchall()
        return [
            {"id": row["id"], "region": row["region"], "name": row["name"], "clusterId": row["cluster_id"], "url": row["url"], "username": row["username"], "password": row["password"], "note": row["note"]}
            for row in rows
        ]

    def replace_clusters(self, clusters: list[dict[str, str]]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        rows = [(item["id"], item["region"], item["name"], item["clusterId"], item["url"], item["username"], item["password"], item["note"], timestamp) for item in clusters]
        with self.connect() as connection:
            connection.execute("DELETE FROM clusters")
            connection.executemany(
                "INSERT INTO clusters (id, region, name, cluster_id, url, username, password, note, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
            )


def clean_cluster(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("集群数据格式无效")
    item = {field: str(value.get(field, "")).strip() for field in CLUSTER_FIELDS}
    item["password"] = str(value.get("password", ""))
    item["id"] = str(value.get("id") or secrets.token_urlsafe(16))
    item["region"] = item["region"] or "未分类"
    if not item["name"] or not item["url"]:
        raise ValueError("每个集群必须包含名称和登录地址")
    if len(item["name"]) > 80 or len(item["url"]) > 2048 or any(len(item[field]) > 500 for field in CLUSTER_FIELDS if field not in {"name", "url"}):
        raise ValueError("字段长度超出限制")
    parsed = urlparse(item["url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("登录地址必须是有效的 HTTP 或 HTTPS 地址")
    return item


def read_json(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as error:
        raise ValueError("无效的请求长度") from error
    if not 0 < length <= MAX_BODY_BYTES:
        raise ValueError("请求数据为空或过大")
    try:
        return json.loads(handler.rfile.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("请求必须是有效的 JSON") from error


def build_handler(app: App) -> type[SimpleHTTPRequestHandler]:
    class Handler(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[{self.log_date_time_string()}] {format % args}")

        def send_json(self, status: HTTPStatus, payload: dict[str, Any], headers: dict[str, str] | None = None) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if headers:
                for name, value in headers.items():
                    self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def cookie_token(self) -> str | None:
            cookie = SimpleCookie(self.headers.get("Cookie"))
            return cookie.get(SESSION_COOKIE).value if cookie.get(SESSION_COOKIE) else None

        def authenticated(self) -> bool:
            if app.is_authenticated(self.cookie_token()):
                return True
            self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "请先登录"})
            return False

        def do_GET(self) -> None:
            if self.path == "/api/session":
                self.send_json(HTTPStatus.OK, {"authenticated": app.is_authenticated(self.cookie_token())})
                return
            if self.path == "/api/clusters":
                if self.authenticated():
                    self.send_json(HTTPStatus.OK, {"clusters": app.list_clusters()})
                return
            super().do_GET()

        def do_POST(self) -> None:
            if self.path == "/api/login":
                try:
                    payload = read_json(self)
                    password = str(payload.get("password", ""))
                except ValueError as error:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                    return
                if not app.verify_password(password):
                    self.send_json(HTTPStatus.UNAUTHORIZED, {"error": "访问密码不正确"})
                    return
                token = app.create_session()
                secure = "; Secure" if isinstance(self.connection, ssl.SSLSocket) else ""
                self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": f"{SESSION_COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={int(SESSION_TTL.total_seconds())}{secure}"})
                return
            if self.path == "/api/logout":
                app.remove_session(self.cookie_token())
                self.send_json(HTTPStatus.OK, {"ok": True}, {"Set-Cookie": f"{SESSION_COOKIE}=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
                return
            if self.path == "/api/clusters":
                if not self.authenticated():
                    return
                try:
                    payload = read_json(self)
                    raw_clusters = payload.get("clusters")
                    if not isinstance(raw_clusters, list) or len(raw_clusters) > 2_000:
                        raise ValueError("集群列表格式无效或数量过多")
                    clusters = [clean_cluster(item) for item in raw_clusters]
                    if len({item["id"] for item in clusters}) != len(clusters):
                        raise ValueError("集群 ID 不能重复")
                    app.replace_clusters(clusters)
                except ValueError as error:
                    self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                    return
                self.send_json(HTTPStatus.OK, {"clusters": app.list_clusters()})
                return
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "接口不存在"})

    return Handler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="启动受认证保护的 Ecloud 集群导航服务。")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认只允许本机访问。")
    parser.add_argument("--port", type=int, default=8765, help="监听端口，默认 8765。")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE, help="SQLite 数据库路径。")
    parser.add_argument("--password-file", type=Path, help="包含访问密码的文件路径。优先于环境变量。")
    parser.add_argument("--certfile", type=Path, help="TLS 证书文件；对外暴露服务时必须配置。")
    parser.add_argument("--keyfile", type=Path, help="TLS 私钥文件；需与 --certfile 配套。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.certfile) != bool(args.keyfile):
        sys.exit("--certfile 与 --keyfile 必须同时设置")
    if args.host not in {"127.0.0.1", "::1", "localhost"} and not args.certfile:
        sys.exit("监听非本机地址时必须配置 --certfile 与 --keyfile，以 HTTPS 保护凭据")
    password = args.password_file.read_text(encoding="utf-8").strip() if args.password_file else os.environ.get("ECLOUD_APP_PASSWORD", "")
    if len(password) < 12:
        sys.exit("请通过 ECLOUD_APP_PASSWORD 或 --password-file 设置至少 12 位的访问密码")
    app = App(args.database.expanduser().resolve(), password)
    server = ThreadingHTTPServer((args.host, args.port), build_handler(app))
    if args.certfile:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.certfile, args.keyfile)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    scheme = "https" if args.certfile else "http"
    print(f"Ecloud 服务已启动：{scheme}://{args.host}:{args.port}/ecloud-login.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
