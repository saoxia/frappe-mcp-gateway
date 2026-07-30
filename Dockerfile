FROM python:3.14.2-slim-bookworm

LABEL org.opencontainers.image.source="https://github.com/saoxia/frappe-mcp-gateway" \
    org.opencontainers.image.description="OAuth-protected MCP gateway for Frappe applications"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 mcp \
    && useradd --system --uid 10001 --gid mcp --home-dir /app mcp

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY frappe_mcp_gateway ./frappe_mcp_gateway

RUN pip install --no-cache-dir .

USER mcp

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=12 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "frappe_mcp_gateway.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
