from __future__ import annotations

import time

import httpx
from mcp.server.auth.provider import AccessToken, TokenVerifier

from frappe_mcp_gateway.settings import Settings


class FrappeTokenVerifier(TokenVerifier):
	def __init__(self, settings: Settings):
		self.settings = settings

	async def verify_token(self, token: str) -> AccessToken | None:
		try:
			async with httpx.AsyncClient(timeout=10) as client:
				response = await client.post(
					f"{self.settings.frappe_base_url}/api/method/"
					"frappe.integrations.oauth2.introspect_token",
					data={"token": token, "token_type_hint": "access_token"},
					headers={"X-Frappe-Site-Name": self.settings.frappe_site},
				)
				response.raise_for_status()
		except (httpx.HTTPError, ValueError):
			return None

		payload = response.json()
		token_data = payload.get("message", payload)
		if not token_data.get("active"):
			return None

		scopes = token_data.get("scope", "").split()
		if self.settings.required_scope not in scopes or "openid" not in scopes:
			return None

		subject = token_data.get("email") or token_data.get("sub")
		if not subject:
			return None

		expires_at = token_data.get("exp")
		if expires_at and int(expires_at) <= int(time.time()):
			return None

		return AccessToken(
			token=token,
			client_id=token_data.get("client_id", "unknown"),
			scopes=scopes,
			expires_at=int(expires_at) if expires_at else None,
			resource=self.settings.mcp_public_url,
			subject=subject,
			claims={
				"email": subject,
				"iss": self.settings.frappe_public_url,
				"roles": token_data.get("roles", []),
			},
		)
