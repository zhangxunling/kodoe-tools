# kodoe-tools

> 日常运维工具与脚本集合

将每个工具独立封装在自己的目录中：代码、运行说明和依赖彼此隔离，方便直接使用、维护与后续扩展。

## 工具索引

| 工具 | 用途 | 运行方式 |
| --- | --- | --- |
| [`ecloud-cluster-navigator`](./ecloud-cluster-navigator/) | 受认证保护的 Ecloud 集群导航与凭据管理服务 | Python 3 标准库 |
| [`hello`](./hello/) | 最小 Python 脚本运行示例 | Python 3 |

## 快速开始

```bash
git clone git@github.com:zhangxunling/kodoe-tools.git
cd kodoe-tools
```

进入目标工具目录，按该目录中的 `README.md` 运行。例如：

```bash
cd hello
python3 hello.py
```

## 目录约定

```text
kodoe-tools/
├── ecloud-cluster-navigator/  # Ecloud 集群导航服务
│   ├── README.md
│   ├── ecloud_server.py
│   └── index.html
├── hello/                     # Python 示例工具
│   ├── README.md
│   └── hello.py
└── README.md                  # 工具索引
```

## 新增工具

新增工具请创建独立目录，并至少提供：

1. 可直接运行的源码或脚本；
2. 该目录内的 `README.md`，包含用途、依赖、启动方式和示例；
3. 必要的依赖清单，例如 `requirements.txt`；
4. 不提交密码、令牌、私钥、证书、生产配置或包含敏感数据的数据库。

运行产生的本地文件请通过根目录 `.gitignore` 或工具目录的 `.gitignore` 排除。

## 安全提示

仓库内的工具可能处理运维入口与凭据。请将密码存入安全的环境变量或受限文件，限制数据文件权限；涉及跨主机访问的服务必须使用 HTTPS，并通过防火墙或反向代理限制访问范围。
