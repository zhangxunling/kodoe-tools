# kodoe-tools

日常运维工作中沉淀的实用工具与脚本集合。项目以轻量、独立、易复用为原则：每个工具应有清晰用途、明确依赖和可直接执行的使用方式。

## 目录说明

| 路径 | 说明 |
| --- | --- |
| `hello.py` | Python 环境与脚本执行示例，输出 `helloe`。 |
| `ecloud-login.html` | Ecloud 集群登录导航页面。 |

## 工具列表

### `ecloud-login.html`

用于集中管理 Ecloud 集群登录入口信息的本地静态页面。

**功能**

- 添加、编辑、删除集群信息
- 保存登录地址、用户名和密码
- 一键复制用户名或密码
- 导入、导出数据备份
- 数据仅存储在当前浏览器的 `localStorage`

**使用方式**

直接使用浏览器打开 `ecloud-login.html` 即可。

> 注意：页面中的敏感信息保存于本机浏览器。请勿在共享设备或不受信任的浏览器环境中使用。

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
