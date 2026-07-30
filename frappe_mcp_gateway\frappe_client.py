from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import jwt
from mcp.server.auth.middleware.auth_context import get_access_token

from frappe_mcp_gateway.settings import Settings


class FrappeClient:
	def __init__(self, settings: Settings):
		self.settings = settings

	async def call(self, method: str, values: dict) -> dict:
		access_token = get_access_token()
		if not access_token or not access_token.subject:
			raise PermissionError("An authenticated MCP user is required")

		async with httpx.AsyncClient(timeout=30) as client:
			response = await client.post(
				f"{self.settings.frappe_base_url}/api/method/{method}",
				json=values,
				headers={
					"X-Frappe-Site-Name": self.settings.frappe_site,
					self.settings.assertion_header: self._assertion(
						access_token.subject,
						access_token.scopes,
					),
				},
			)
		response.raise_for_status()
		payload = response.json()
		if payload.get("exc_type"):
			raise RuntimeError(payload.get("exception") or payload["exc_type"])
		return payload.get("message", payload)

	def _assertion(self, subject: str, scopes: list[str]) -> str:
		now = datetime.now(UTC)
		return jwt.encode(
			{
				"sub": subject,
				"iss": self.settings.assertion_issuer,
				"aud": self.settings.assertion_audience,
				"scope": " ".join(scopes),
				"iat": now,
				"exp": now + timedelta(seconds=60),
				"jti": str(uuid4()),
			},
			self.settings.assertion_secret,
			algorithm="HS256",
		)
