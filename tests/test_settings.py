import pytest

from frappe_mcp_gateway.settings import Settings


def test_settings_reject_short_assertion_secret(monkeypatch):
	_set_required_environment(monkeypatch, assertion_secret="short")

	with pytest.raises(RuntimeError, match="at least 32"):
		Settings.from_environment()


def test_settings_normalize_urls_and_parse_lists(monkeypatch):
	_set_required_environment(monkeypatch)

	settings = Settings.from_environment()

	assert settings.frappe_base_url == "http://personal:8000"
	assert settings.allowed_hosts == ["pip.lly.info", "127.0.0.1:*"]
	assert settings.assertion_header == "X-Personal-MCP-Assertion"


def _set_required_environment(monkeypatch, *, assertion_secret="test-secret-that-is-at-least-32-characters"):
	values = {
		"FRAPPE_BASE_URL": "http://personal:8000/",
		"FRAPPE_PUBLIC_URL": "https://pip.lly.info/",
		"FRAPPE_SITE": "pip.lly.info",
		"MCP_PUBLIC_URL": "https://pip.lly.info/mcp/",
		"MCP_ASSERTION_SECRET": assertion_secret,
		"MCP_ASSERTION_HEADER": "X-Personal-MCP-Assertion",
		"MCP_ALLOWED_HOSTS": "pip.lly.info,127.0.0.1:*",
		"MCP_ALLOWED_ORIGINS": "https://pip.lly.info",
	}
	for name, value in values.items():
		monkeypatch.setenv(name, value)
