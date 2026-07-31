# 开发新工具包

工具包把 MCP 工具映射到明确的 Frappe whitelisted method。通用认证和断言
逻辑不应复制到每个工具中。

## 目录约定

```text
frappe_mcp_gateway/
  tools/
    __init__.py
    personal_health.py
    erpnext_sales.py
```

一个工具包导出注册函数：

```python
from mcp.server import MCPServer

from frappe_mcp_gateway.frappe_client import FrappeClient


def register_sales_tools(server: MCPServer, client: FrappeClient):
    @server.tool()
    async def list_quotations(limit: int = 20) -> dict:
        """List quotations visible to the authenticated Frappe user."""
        return await client.call(
            "my_app.sales.mcp_api.list_quotations",
            {"limit": limit},
        )
```

然后在 `server.py` 中注册：

```python
register_sales_tools(mcp, frappe_client)
```

`FrappeClient.call()` 自动读取当前 MCP 用户，生成短期内部断言并调用 Frappe
method。工具代码不应自行解析或转发 OAuth token。

## 工具设计原则

- 工具名表达业务意图，例如 `create_quotation`，而不是 `insert_document`。
- 参数使用类型和 Pydantic `Field` 约束范围、格式和说明。
- 查询工具必须限制返回数量。
- 写工具需要明确文档字符串，要求客户端先向用户确认。
- 写工具接收 `client_request_id`，Frappe 端用它实现幂等。
- 不接受任意 DocType、method 路径、SQL、脚本或过滤表达式。
- 返回稳定的结构化结果，避免把完整 Frappe 文档和敏感字段直接返回。

## 读写分离

对有副作用的动作，建议拆成两个工具：

1. `preview_*` 或只读查询，向用户展示即将发生的变化。
2. `create_*`、`update_*` 或 `submit_*`，仅在用户明确确认后调用。

提示词不是安全边界。即使 MCP server instructions 要求确认，Frappe API
仍必须校验权限、状态转换和业务规则。

## 测试建议

网关单元测试至少覆盖：

- 工具参数约束；
- method 路径和 payload 映射；
- 内部断言包含正确 subject、scope、issuer 和 audience；
- Frappe HTTP 错误被转换为明确失败。

Frappe App 集成测试至少覆盖：

- 当前用户权限与所有者隔离；
- 写操作幂等；
- Guest 和越权用户被拒绝；
- 断言过期与重放被拒绝；
- 输入边界和业务规则。

## 通用 ERPNext 工具包

网关核心可以复用于普通 ERPNext。建议按领域拆包：

- `erpnext_sales`
- `erpnext_buying`
- `erpnext_stock`
- `erpnext_accounts`
- `erpnext_projects`

每个部署只启用需要的工具包和 scope，避免一个 OAuth 授权自动获得全部 ERP
能力。高风险动作（提交单据、付款、库存调整、删除）应使用更细 scope，并
在 Frappe 端增加审批或角色约束。
