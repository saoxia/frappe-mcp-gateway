# 部署与运维

## 推荐拓扑

生产环境推荐将 Frappe、Redis、数据库、MCP Gateway 和 Nginx 分别运行，
并通过 Docker Compose 私有网络连接。网关不使用 host 网络。

只需发布以下端口：

- Nginx：`80`、`443`；
- MCP Gateway：可选映射到 `127.0.0.1:8100`，不要直接暴露公网；
- Frappe 与 Redis：仅监听本机或内部容器网络。

## Docker Compose 示例

```yaml
services:
  mcp:
    build:
      context: /srv/frappe-mcp-gateway
    image: frappe-mcp-gateway:runtime
    container_name: frappe-mcp-gateway
    restart: unless-stopped
    env_file:
      - /srv/my-stack/mcp.env
    ports:
      - "127.0.0.1:8100:8000"
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)
      interval: 10s
      timeout: 3s
      retries: 12
```

如果 Frappe 和网关在同一 Compose network 中，`FRAPPE_BASE_URL` 可设置为
`http://frappe:8000`。独立 Compose project 需要显式加入同一个 external
network，或使用仅监听本机的端口访问。

## Nginx 示例

```nginx
upstream frappe-mcp-gateway {
    server mcp:8000 fail_timeout=60s;
}

location = /.well-known/oauth-protected-resource/mcp {
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://frappe-mcp-gateway;
}

location /mcp {
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 3600;
    proxy_pass http://frappe-mcp-gateway;
}
```

必须使用 HTTPS。公网域名应同时出现在 `MCP_PUBLIC_URL`、
`MCP_ALLOWED_HOSTS` 和 `MCP_ALLOWED_ORIGINS` 中。

## 首次部署

```sh
git clone https://github.com/saoxia/frappe-mcp-gateway.git \
  /srv/frappe-mcp-gateway
cd /srv/frappe-mcp-gateway
cp .env.example /srv/my-stack/mcp.env
chmod 600 /srv/my-stack/mcp.env
```

编辑环境文件后：

```sh
cd /srv/my-stack
docker compose config --quiet
docker compose build mcp
docker compose up -d mcp
docker compose ps
```

## 更新

先构建，再替换运行容器：

```sh
cd /srv/frappe-mcp-gateway
git pull --ff-only origin main

cd /srv/my-stack
docker compose build mcp
docker compose up -d --no-deps --force-recreate mcp
docker compose ps
```

更新后检查 Nginx 配置并平滑 reload：

```sh
docker exec nginx nginx -t
docker exec nginx nginx -s reload
```

## 验证

```sh
curl -fsS https://erp.example.com/api/method/ping
curl -fsS https://erp.example.com/.well-known/oauth-protected-resource/mcp
curl -i \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{}' \
  https://erp.example.com/mcp
```

最后一个未授权请求应返回 `401`，并包含 `WWW-Authenticate: Bearer`。还应使用
测试用户完成一次真实 OAuth 登录、工具读取、写入确认和撤销授权测试。

## 日志

```sh
docker compose logs --tail=200 mcp
docker compose logs --since=10m mcp
```

日志中不应输出：

- `Authorization` header；
- OAuth access token；
- 完整内部断言；
- `MCP_ASSERTION_SECRET`；
- Frappe session cookie。

## 常见问题

### MCP 请求返回 401

检查 token 是否 active，是否同时包含 `openid` 和业务 scope，以及
`FRAPPE_BASE_URL`、`FRAPPE_SITE` 是否指向正确站点。

### Frappe 内部 API 返回 401/403

检查 assertion secret、issuer、audience、header 和 scope 是否在两端一致，
并确认 `sub` 对应启用中的用户。

### Host 或 Origin 被拒绝

将实际公网域名加入 `MCP_ALLOWED_HOSTS` 和 `MCP_ALLOWED_ORIGINS`。不要为了
快速修复而使用通配的任意 host/origin。

### 撤销后仍能访问

确认网关调用的是当前 Frappe 站点的 introspection endpoint，且 Frappe
撤销操作会使 access token 变为 inactive。检查反向代理是否错误缓存了
introspection 或 MCP 响应。

## 回滚

保留上一个已验证的 Git commit 和镜像标签：

```sh
cd /srv/frappe-mcp-gateway
git checkout <previous-commit>

cd /srv/my-stack
docker compose build mcp
docker compose up -d --no-deps --force-recreate mcp
```

回滚不应覆盖 `mcp.env`。若回滚版本使用不同的 assertion 配置，必须同步调整
Frappe 站点配置。
