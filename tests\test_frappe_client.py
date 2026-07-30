import jwt

from frappe_mcp_gateway.frappe_client import FrappeClient
from frappe_mcp_gateway.settings import Settings


def test_internal_assertion_contains_identity_and_scope():
	settings = Settings(
		frappe_base_url="http://personal:8000",
		frappe_public_url="https://pip.lly.info",
		frappe_site="pip.lly.info",
		mcp_public_url="https://pip.lly.info/mcp",
		assertion_secret="test-secret-that-is-at-least-32-characters",
		assertion_issuer="frappe-mcp-gateway",
		assertion_audience="personal-frappe-api",
		assertion_header="X-Personal-MCP-Assertion",
		required_scope="personal:mcp",
		allowed_hosts=["pip.lly.info"],
		allowed_origins=["https://pip.lly.info"],
	)

	assertion = FrappeClient(settings)._assertion(
		"user@example.com",
		["openid", "personal:mcp"],
	)
	claims = jwt.decode(
		assertion,
		settings.assertion_secret,
		algorithms=["HS256"],
		audience=settings.assertion_audience,
		issuer=settings.assertion_issuer,
	)

	assert claims["sub"] == "user@example.com"
	assert claims["scope"] == "openid personal:mcp"
	assert claims["jti"]
