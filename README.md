# kodoe-tools

日常运维工作中沉淀的实用工具与脚本集合。项目以轻量、独立、易复用为原则：每个工具应有清晰用途、明确依赖和可直接执行的使用方式。

## 目录说明

| 路径 | 说明 |
| --- | --- |
| `hello.py` | Python 环境与脚本执行示例，输出 `helloe`。 |
| `ecloud-login.html` | Ecloud 集群登录导航前端页面。 |
| `ecloud_server.py` | 受密码保护的 Ecloud 集群导航服务端。 |

## 工具列表

### `ecloud-login.html` 与 `ecloud_server.py`

用于集中管理 Ecloud 集群登录入口信息的受认证服务。集群数据保存在服务端 SQLite 数据库，因此可由不同浏览器或主机访问同一份列表。

**功能**

- 访问密码登录，使用 `HttpOnly`、`SameSite=Strict` 会话 Cookie
- 服务端保存集群信息，支持添加、编辑、删除、搜索、导入与导出
- 一键复制用户名或密码
- 服务默认仅监听本机；对外访问时强制要求 TLS 证书

**启动方式**

```bash
cd kodoe-tools
export ECLOUD_APP_PASSWORD='请设置至少12位的强密码'
python3 ecloud_server.py
```

然后访问：`http://127.0.0.1:8765/ecloud-login.html`

如需在其他主机访问，必须配置 HTTPS：

```bash
python3 ecloud_server.py \
  --host 0.0.0.0 \
  --certfile /path/to/fullchain.pem \
  --keyfile /path/to/privkey.pem
```

> 注意：`ecloud-data.sqlite3` 包含集群凭据，已被 `.gitignore` 排除。请设置文件权限、定期备份数据库，且不要提交数据库、密码文件、证书或私钥。

### `hello.py`

Python 脚本示例，用于验证脚本运行环境。

```bash
python3 hello.py
```

## 新增工具规范

新增工具时请尽量遵循以下约定：

1. 按用途创建独立目录，或使用清晰的文件名。
2. 在本 README 的“工具列表”补充用途、依赖和使用方式。
3. 脚本应包含必要的参数说明、错误提示与使用示例。
4. 不要提交密码、令牌、密钥、生产环境配置或其他敏感信息。
5. 依赖较多的工具应提供对应的依赖清单，例如 `requirements.txt`。

## 快速开始

```bash
git clone git@github.com:zhangxunling/kodoe-tools.git
cd kodoe-tools
python3 hello.py
```
