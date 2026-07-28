# SHUNYA Production Configuration Guide

## Architecture

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  nginx (port 443)                                            │
│  ├─ SSL termination (TLSv1.2, TLSv1.3)                      │
│  ├─ Security headers (CSP, HSTS, XSS, etc.)                 │
│  ├─ WebSocket proxy                                          │
│  ├─ Gzip compression                                         │
│  ├─ Request limits (16 MB)                                   │
│  └─ Static asset delivery (immutable, 365d cache)            │
└──────────────────────────┬───────────────────────────────────┘
                           │ proxy_pass http://web:8000
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  gunicorn (4 workers)                                        │
│  ├─ WSGI: wsgi:app                                          │
│  ├─ Timeout: 120s                                           │
│  ├─ Access log: stdout                                      │
│  └─ Error log: stdout                                       │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Flask Application                                          │
│  ├─ /health — full runtime check                            │
│  ├─ /ready — readiness probe                                │
│  ├─ /live — liveness probe                                  │
│  ├─ /api/v1/space/* — Space API                             │
│  ├─ /static/* — immutable assets                            │
│  └─ /* — all other routes                                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                 │
│  └─ Database: shunya_db                                     │
└──────────────────────────────────────────────────────────────┘
```

## nginx Configuration

Configuration file: `infrastructure/nginx/production.conf`

### Key Settings

| Setting | Value | Purpose |
|---|---|---|
| `client_max_body_size` | 16M | Upload limit |
| `ssl_protocols` | TLSv1.2 TLSv1.3 | Modern TLS only |
| `gzip_types` | text/css, javascript, json, svg, woff2 | Compression |
| `expires` (static) | 365d | Long-term caching |
| `proxy_read_timeout` | 120s | Long request support |

### Security Headers

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `Permissions-Policy` | Restricted to `geolocation=(), microphone=(self), camera=()` |

## Docker Compose

Configuration file: `docker-compose.yml`

### Services

| Service | Image | Ports |
|---|---|---|
| web | Build from Dockerfile | 8000 |
| postgres | pgvector/pgvector:0.8.0-pg16 | 5432 |
| nginx | nginx:1-alpine | 80, 443 |

## Health Endpoints

| Endpoint | Purpose | Expected Response |
|---|---|---|
| `GET /health` | Full runtime check | `{"status": "ok", ...}` |
| `GET /ready` | Readiness probe | `{"status": "ok", "database": "ready"}` |
| `GET /live` | Liveness probe | `{"status": "alive"}` |

## Production Security Checklist

- [ ] `SECRET_KEY` is a strong random value (not default)
- [ ] `DEBUG` is `false`
- [ ] `FLASK_ENV` is `production`
- [ ] HTTPS is enforced (SSL redirect)
- [ ] HSTS header is set with `includeSubDomains`
- [ ] Session cookies are `Secure`, `HttpOnly`, `SameSite=Lax`
- [ ] CSRF protection is enabled
- [ ] Rate limiting is enabled
- [ ] Upload limits are set (16 MB)
- [ ] Trusted proxies are configured
- [ ] Sentry error tracking is configured (optional but recommended)
- [ ] Database password is strong (not default)
- [ ] `.env` is in `.gitignore` and never committed
- [ ] Logs do not contain secrets or PII