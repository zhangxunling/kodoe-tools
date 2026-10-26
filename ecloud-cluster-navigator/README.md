# Ecloud 集群导航

受访问密码保护的集群入口与凭据管理工具。数据保存在服务端 SQLite 数据库，多个浏览器或主机可访问同一份集群列表。

## 功能

- 访问密码登录，使用 `HttpOnly`、`SameSite=Strict` 会话 Cookie；
- 管理集群的区域、名称、地址、用户名、密码与备注；
- 搜索、添加、编辑、删除、导入和导出集群信息；
- 默认仅监听本机；监听外部地址时强制启用 TLS。

## 要求

- Python 3.10 或更高版本；
- 无第三方依赖。

## 本机启动

```bash
cd ecloud-cluster-navigator
export ECLOUD_APP_PASSWORD='请设置至少12位的强密码'
python3 ecloud_server.py
```

浏览器打开：`http://127.0.0.1:8765/index.html`

## 跨主机访问

跨主机传输凭据必须使用 HTTPS。服务监听非本机地址时，未提供证书会拒绝启动：

```bash
export ECLOUD_APP_PASSWORD='请设置至少12位的强密码'
python3 ecloud_server.py \
  --host 0.0.0.0 \
  --port 8765 \
  --certfile /path/to/fullchain.pem \
  --keyfile /path/to/privkey.pem
```

建议通过受访问控制的反向代理或防火墙，仅开放可信网络来源。

## 数据与备份

默认数据库为当前目录的 `ecloud-data.sqlite3`，可通过 `--database` 指定路径：

```bash
python3 ecloud_server.py --database /secure/path/ecloud.sqlite3
```

数据库和导出的 JSON 均可能包含明文凭据：

- 不要提交到 Git；
- 设置仅服务账户可读写的文件权限；
- 将备份保存到受加密与访问控制保护的位置；
- 遗失或泄露时，请及时轮换相关凭据。

## 常用参数

```text
--host HOST                 监听地址，默认 127.0.0.1
--port PORT                 监听端口，默认 8765
--database PATH             SQLite 数据库路径
--password-file PATH        从文件读取访问密码
--certfile PATH --keyfile PATH  配置 HTTPS 证书与私钥
```
