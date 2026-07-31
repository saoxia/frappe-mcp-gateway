# 配置参考

网关只从环境变量读取配置。可以复制仓库根目录的 `.env.example` 作为起点。

## Frappe 连接

| 变量 | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `FRAPPE_BASE_URL` | 是 | `http://personal:8000` | 网关访问 Frappe 的内部地址 |
| `FRAPPE_PUBLIC_URL` | 是 | `https://erp.example.com` | OAuth issuer 和用户可访问的站点地址 |
| `FRAPPE_SITE` | 是 | `erp.example.com` | 通过 `X-Frappe-Site-Name` 发送的站点名 |

`FRAPPE_BASE_URL` 可以是 Docker service DNS。不要在其中包含结尾 `/`。

## MCP 公网地址

| 变量 | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `MCP_PUBLIC_URL` | 是 | `https://erp.example.com/mcp` | 客户端访问的 MCP resource URL |
| `MCP_REQUIRED_SCOPE` | 否 | `erp:mcp` | 业务 scope，默认 `frappe:mcp` |
| `MCP_ALLOWED_HOSTS` | 是 | `erp.example.com,erp.example.com:*` | MCP SDK transport security host 白名单 |
| `MCP_ALLOWED_ORIGINS` | 是 | `https://erp.example.com` | 允许的 Web Origin |

网关同时要求 `openid` 和 `MCP_REQUIRED_SCOPE`。相应 scope 必须在 Frappe
OAuth Client/Provider 中可用。

## 内部断言

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `MCP_ASSERTION_SECRET` | 是 | 无 | HS256 密钥，至少 32 个字符 |
| `MCP_ASSERTION_ISSUER` | 否 | `frappe-mcp-gateway` | 断言 issuer |
| `MCP_ASSERTION_AUDIENCE` | 否 | `frappe-api` | 断言 audience |
| `MCP_ASSERTION_HEADER` | 否 | `X-Frappe-MCP-Assertion` | 发送断言的 HTTP header |

Frappe App 中配置的 secret、issuer、audience 和 header 必须与网关完全一致。

生成随机密钥示例：

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

不要在 shell 历史、镜像层、Compose 文件或 Git 中直接写入真实密钥。

## 示例

```dotenv
FRAPPE_BASE_URL=http://frappe:8000
FRAPPE_PUBLIC_URL=https://erp.example.com
FRAPPE_SITE=erp.example.com
MCP_PUBLIC_URL=https://erp.example.com/mcp

MCP_ASSERTION_SECRET=replace-with-a-random-secret-of-at-least-32-characters
MCP_ASSERTION_ISSUER=frappe-mcp-gateway
MCP_ASSERTION_AUDIENCE=erp-frappe-api
MCP_ASSERTION_HEADER=X-Frappe-MCP-Assertion

MCP_REQUIRED_SCOPE=erp:mcp
MCP_ALLOWED_HOSTS=erp.example.com,erp.example.com:*,127.0.0.1,127.0.0.1:*
MCP_ALLOWED_ORIGINS=https://erp.example.com
```

## 启动时校验

以下情况会导致应用拒绝启动：

- 缺少任一必填变量；
- `MCP_ASSERTION_SECRET` 少于 32 个字符；
- host 或 origin 白名单为空。

部署后可以通过 `/health` 检查进程，但该接口不代表 Frappe OAuth 或业务 API
一定可用。生产监控还应执行一次受控的 OAuth/MCP 端到端检查。
