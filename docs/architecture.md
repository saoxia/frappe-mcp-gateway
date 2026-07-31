# 架构与安全模型

## 组件职责

Frappe MCP Gateway 被设计为独立的 OAuth Resource Server 和 MCP
sidecar。各组件职责如下：

| 组件 | 职责 |
| --- | --- |
| MCP 客户端 | 发起 OAuth 授权、保存访问令牌、调用 MCP 工具 |
| Frappe | 用户登录、OAuth 授权、token introspection、角色与业务权限 |
| MCP Gateway | MCP 协议、令牌校验、工具注册、内部断言签发 |
| Frappe App | 内部断言校验、防重放、参数校验和业务操作 |
| 反向代理 | TLS 终止、域名与公网路由 |

网关本身不需要数据库。它不会保存 OAuth 令牌、用户密码或用户会话。

## 身份传递

客户端在 `Authorization: Bearer <token>` 中发送 Frappe OAuth 访问令牌。
网关通过 Frappe 标准 `introspect_token` 接口确认：

- `active` 为真；
- 令牌尚未过期；
- 同时包含 `openid` 和 `MCP_REQUIRED_SCOPE`；
- 响应包含 `email` 或 `sub`，可映射为 Frappe 用户。

校验成功后，网关不会把原始访问令牌发送给业务 API，而是生成 HS256 JWT
内部断言：

| Claim | 含义 |
| --- | --- |
| `sub` | 已通过 OAuth 验证的 Frappe 用户 |
| `iss` | `MCP_ASSERTION_ISSUER` |
| `aud` | `MCP_ASSERTION_AUDIENCE` |
| `scope` | 已验证的 OAuth scopes |
| `iat` | 签发时间 |
| `exp` | 过期时间，当前为签发后 60 秒 |
| `jti` | 每次调用唯一的随机 ID |

断言通过 `MCP_ASSERTION_HEADER` 指定的请求头发送给 Frappe App。

## 为什么不直接转发 OAuth Token

内部断言缩小了令牌暴露范围：

- 业务 API 无需接触可重复使用的 OAuth access token。
- 断言只能用于指定 audience。
- 断言 60 秒后失效。
- Frappe App 可以记录并拒绝重复 `jti`。
- 网关只向预先编码的业务方法发起请求。

断言密钥仍属于高敏感配置，应通过 Docker secret、权限为 `0600` 的环境
文件或秘密管理服务提供，不能提交到 Git。

## 撤销授权

网关会在每次 MCP 请求时 introspect access token，而不是长期缓存授权结果。
用户在 Frappe 撤销 OAuth 授权后，token 会变为 inactive，下一次 MCP 请求
返回 401。

撤销由 Frappe 负责，因此不需要在网关中再实现一套用户或授权管理系统。

## 权限边界

OAuth scope 只是第一层准入条件，不替代 Frappe 业务权限。Frappe App 的
内部 API 仍应：

1. 从已验证的断言 `sub` 建立用户上下文。
2. 使用 Frappe permission API 或正常文档操作执行权限检查。
3. 对按所有者隔离的数据再次约束 owner。
4. 验证所有输入，不能信任 MCP 客户端生成的参数。
5. 对写操作提供幂等键，并记录审计信息。

切勿提供能够以 Administrator 身份执行任意 method、SQL 或 DocType CRUD
的通用工具。

## 网络模型

推荐的容器网络路径为：

```text
Internet
   |
   v
Reverse proxy :443
   |             \
   v              v
MCP Gateway     Frappe Web
   |
   v
Frappe internal HTTP API
```

网关端口应只监听 `127.0.0.1` 或内部容器网络。公网只开放反向代理的 443。
`MCP_ALLOWED_HOSTS` 和 `MCP_ALLOWED_ORIGINS` 必须限制为实际域名。

## 信任假设

- 反向代理与网关之间的网络受控制。
- Frappe introspection endpoint 是可信的。
- 网关和 Frappe App 持有相同断言密钥。
- Frappe App 正确执行签名、issuer、audience、过期时间和 `jti` 校验。
- TLS 私钥、断言密钥和 OAuth client secret 不进入仓库或日志。
