from __future__ import annotations

from mcp.server import MCPServer
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from frappe_mcp_gateway.auth import FrappeTokenVerifier
from frappe_mcp_gateway.frappe_client import FrappeClient
from frappe_mcp_gateway.settings import Settings
from frappe_mcp_gateway.tools.personal_health import register_personal_health_tools

settings = Settings.from_environment()
frappe_client = FrappeClient(settings)
mcp = MCPServer(
	name="Frappe MCP Gateway",
	instructions=(
		"Use Frappe tools for the authenticated user. "
		"Ask for confirmation before creating or changing business records."
	),
	token_verifier=FrappeTokenVerifier(settings),
	auth=AuthSettings(
		issuer_url=AnyHttpUrl(settings.frappe_public_url),
		resource_server_url=AnyHttpUrl(settings.mcp_public_url),
		required_scopes=["openid", settings.required_scope],
	),
)
register_personal_health_tools(mcp, frappe_client)


async def health(_request: Request) -> JSONResponse:
	return JSONResponse({"status": "ok"})


app = mcp.streamable_http_app(
	transport_security=TransportSecuritySettings(
		allowed_hosts=settings.allowed_hosts,
		allowed_origins=settings.allowed_origins,
	)
)
app.routes.insert(0, Route("/health", health, methods=["GET"]))
