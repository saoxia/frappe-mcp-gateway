# Frappe MCP Gateway

An OAuth-protected MCP sidecar for Frappe applications. It uses the official
MCP Python SDK and keeps MCP transport dependencies outside the Frappe runtime.

The gateway validates a Frappe OAuth access token on every MCP request. It does
not forward that token to business APIs. Instead, it signs a one-time,
60-second internal assertion containing the authenticated Frappe user.

## Current tool packs

- `personal_health`: read and create Personal health body metrics.

The authentication, transport, assertion, and Frappe HTTP client layers are
generic. Additional ERPNext or Frappe tool packs can be added under
`frappe_mcp_gateway/tools`.

## Required Frappe integration

The target Frappe app must provide:

- OAuth token introspection at Frappe's standard introspection endpoint.
- An internal API that verifies the gateway assertion.
- OAuth scopes matching `MCP_REQUIRED_SCOPE`.

The initial Personal tool pack calls:

- `personal.health.sidecar_api.create_health_body_metrics`
- `personal.health.sidecar_api.get_health_body_metrics`

## Run with Docker

Create an environment file from `.env.example`, use a random assertion secret
of at least 32 characters, and configure the same secret in the target Frappe
site.

```sh
docker build -t frappe-mcp-gateway:runtime .
docker run --rm \
  --env-file .env \
  -p 127.0.0.1:8100:8000 \
  frappe-mcp-gateway:runtime
```

The endpoints are:

- `/health`: container health check.
- `/mcp`: streamable HTTP MCP endpoint.
- `/.well-known/oauth-protected-resource/mcp`: OAuth protected-resource
  metadata.

## Test

```sh
python -m pip install -e . pytest
pytest
```

The production deployment in `saoxia/frappe-personal` builds this repository
from `/srv/frappe-mcp-gateway`.
