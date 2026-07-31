# 接入 Frappe App

本项目提供通用 MCP 网关，但目标 Frappe App 必须实现与自身业务一致的授权
scope、内部断言验证和白名单业务 API。

## 1. 配置 OAuth

Frappe 作为 Authorization Server。接入方需要：

1. 为 MCP 客户端创建 OAuth Client。
2. 允许 `openid` 和业务 scope，例如 `erp:mcp`。
3. 确保标准 token introspection endpoint 可由网关访问。
4. 根据客户端能力配置 redirect URI 或动态客户端注册。
5. 为用户提供已授权应用列表及撤销入口。

网关调用的标准 introspection method：

```text
frappe.integrations.oauth2.introspect_token
```

## 2. 配置共享断言参数

在站点配置或秘密管理系统中保存：

- assertion secret；
- issuer；
- audience；
- assertion header；
- 必需 scope。

这些值必须与网关环境变量一致。生产环境修改 secret 时，应支持短时间的新旧
密钥轮换，避免正在执行的请求失败。

## 3. 实现断言验证

Frappe App 收到内部业务请求时，至少验证：

- 算法固定为 HS256，不能从 token header 动态接受任意算法；
- 签名正确；
- `iss` 与配置一致；
- `aud` 与配置一致；
- `iat` 合理且 `exp` 尚未过期；
- `exp - iat` 不超过允许窗口；
- `scope` 包含业务 scope；
- `sub` 对应启用中的 Frappe 用户；
- `jti` 未被使用过。

验证成功后，在执行具体业务逻辑前切换到 `sub` 对应用户。无论断言是否有效，
都不能用 Guest 或 Administrator 默认上下文继续执行。

## 4. 防止重放

每个内部断言都包含唯一 `jti`。Frappe App 应通过 Redis cache 的原子
`set-if-not-exists` 或等效机制保存已使用的 `jti`，TTL 至少覆盖断言有效期。
相同 `jti` 的第二次请求必须失败。

如果多个 Frappe worker 共同提供服务，防重放状态必须共享，不能只保存在
单个 Python 进程内存中。

## 5. 编写白名单业务 API

一个 MCP 工具应映射到明确的 Frappe method，例如：

```text
my_app.sales.mcp_api.create_quotation
my_app.sales.mcp_api.list_quotations
```

业务 method 应：

- 只接受业务需要的字段；
- 使用 Frappe 文档 API 和正常权限检查；
- 限制查询数量和时间范围；
- 对写操作使用 `client_request_id` 实现幂等；
- 返回稳定、最小化的 JSON 结构；
- 不返回 OAuth token、API secret、密码或无关个人数据。

不要暴露接受任意 method 名、DocType、过滤器或 SQL 的代理接口。

## 6. 撤销与审计

撤销 OAuth 授权后，Frappe introspection 应返回 inactive。由于网关每次请求
都会 introspect，撤销会在下一次 MCP 调用生效。

建议为写操作记录：

- Frappe 用户；
- OAuth client ID；
- MCP 工具名；
- 业务文档名称；
- `client_request_id`；
- 请求时间与结果；
- 必要时记录用户确认信息，但不要记录 token 或完整断言。

## 7. 集成测试清单

- 有效 token 可以调用授权工具。
- 缺少 `openid` 或业务 scope 时返回 401/403。
- 已过期或已撤销 token 被拒绝。
- 断言签名、issuer、audience 或 header 不匹配时被拒绝。
- 过期断言和重复 `jti` 被拒绝。
- 用户只能访问自己有权限的数据。
- Guest 无法调用内部 API。
- 重复 `client_request_id` 不会创建重复业务文档。
