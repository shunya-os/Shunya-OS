# SHUNYA Environment Guide

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     shunyaos.com                         │
│   Identity · Documentation · Product · Authentication    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    app.shunyaos.com                      │
│              Universal SHUNYA Runtime                    │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Space   │ │  Graph   │ │  Kernel  │ │ Runtimes │   │
│  │   API    │ │  Engine  │ │  Layer   │ │(Plan,Exec│   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │
│  │  Health  │ │  Auth    │ │  Static  │                  │
│  │ /ready   │ │  Session │ │  Assets  │                  │
│  │ /live    │ │  CSRF    │ │  /static │                  │
│  └──────────┘ └──────────┘ └──────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Environment Matrix

| Property | Development | Testing | Production |
|---|---|---|---|
| Database | PostgreSQL (local) | SQLite :memory: | PostgreSQL (managed) |
| Debug | true | false | false |
| Rate Limiting | disabled | disabled | enabled |
| SSL | false | false | true |
| Workers | 1 | 1 | 4 |
| Log Level | DEBUG | WARNING | INFO |
| Session | HTTP | HTTP | HTTPS only |

## Environment Variables

### Required

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Flask session signing key | (random 64-char hex) |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |

### Security

| Variable | Default | Description |
|---|---|---|
| `SESSION_COOKIE_SECURE` | `true` (prod) | HTTPS-only cookies |
| `SESSION_COOKIE_HTTPONLY` | `true` | Prevent JS access to cookies |
| `SESSION_COOKIE_SAMESITE` | `Lax` | CSRF protection |
| `WTF_CSRF_ENABLED` | `true` (prod) | CSRF token validation |
| `TRUSTED_PROXIES` | RFC1918 subnets | Reverse proxy IPs |
| `SSL_REDIRECT` | `true` (prod) | HTTP→HTTPS redirect |

### Application

| Variable | Default | Description |
|---|---|---|
| `SHUNYA_ENVIRONMENT` | `production` | Runtime environment label |
| `FLASK_ENV` | `production` | Flask environment |
| `DEBUG` | `false` | Debug mode |
| `MAX_CONTENT_LENGTH` | `16777216` | 16 MB upload limit |

### Monitoring

| Variable | Default | Description |
|---|---|---|
| `SENTRY_DSN` | (empty) | Sentry error tracking |
| `HEALTH_TOKEN` | (empty) | Health endpoint auth token |

## Setting Up a New Environment

```bash
# 1. Copy the environment template
cp infrastructure/environments/production.env .env

# 2. Generate secrets
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')" >> .env
python3 -c "import secrets; print(f'HEALTH_TOKEN={secrets.token_hex(16)}')" >> .env

# 3. Edit .env with your database credentials
# 4. Verify configuration
source .venv/bin/activate
python3 -c "from app import create_app; app = create_app(); print('Config OK')"
```