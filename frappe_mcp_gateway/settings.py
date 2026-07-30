from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
	frappe_base_url: str
	frappe_public_url: str
	frappe_site: str
	mcp_public_url: str
	assertion_secret: str
	assertion_issuer: str
	assertion_audience: str
	assertion_header: str
	required_scope: str
	allowed_hosts: list[str]
	allowed_origins: list[str]

	@classmethod
	def from_environment(cls) -> "Settings":
		settings = cls(
			frappe_base_url=_required("FRAPPE_BASE_URL").rstrip("/"),
			frappe_public_url=_required("FRAPPE_PUBLIC_URL").rstrip("/"),
			frappe_site=_required("FRAPPE_SITE"),
			mcp_public_url=_required("MCP_PUBLIC_URL").rstrip("/"),
			assertion_secret=_required("MCP_ASSERTION_SECRET"),
			assertion_issuer=os.getenv("MCP_ASSERTION_ISSUER", "frappe-mcp-gateway"),
			assertion_audience=os.getenv("MCP_ASSERTION_AUDIENCE", "frappe-api"),
			assertion_header=os.getenv("MCP_ASSERTION_HEADER", "X-Frappe-MCP-Assertion"),
			required_scope=os.getenv("MCP_REQUIRED_SCOPE", "frappe:mcp"),
			allowed_hosts=_csv("MCP_ALLOWED_HOSTS"),
			allowed_origins=_csv("MCP_ALLOWED_ORIGINS"),
		)
		if len(settings.assertion_secret) < 32:
			raise RuntimeError("MCP_ASSERTION_SECRET must contain at least 32 characters")
		return settings


def _required(name: str) -> str:
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"{name} is required")
	return value


def _csv(name: str) -> list[str]:
	return [value.strip() for value in _required(name).split(",") if value.strip()]
