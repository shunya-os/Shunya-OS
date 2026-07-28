# SHUNYA Deployment Guide

## Canonical Application Surface

```
app.shunyaos.com  ←  All authenticated users enter SHUNYA here
```

## Public Platform Separation

```
shunyaos.com                   app.shunyaos.com
  │                              │
  ├─ Identity                    ├─ Universal Runtime
  ├─ Documentation               ├─ Space API
  ├─ Product narrative           ├─ Health endpoints
  └─ Authentication              └─ All authenticated features
```

The public site shall never contain application logic.  
The application runtime shall never depend on marketing assets.

## Deployment Sequence

### Prerequisites

- Docker and docker-compose installed
- Git access to the SHUNYA repository
- `.env` file with production secrets (never commit to source)
- SSL certificates in `/etc/letsencrypt/live/app.shunyaos.com/`

### Manual Deployment

```bash
# 1. Fetch
cd /home/shunya-deploy/shunya_os
git fetch origin main
git checkout main
git pull origin main

# 2. Install
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# 3. Migration
alembic upgrade head

# 4. Restart
docker-compose up -d --build --no-deps web

# 5. Verification
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

# 6. Health Check
curl -s http://127.0.0.1:8000/ready
```

### Automated Deployment

```bash
./infrastructure/scripts/deploy.sh production
```

## Environment Files

| Environment | File | Purpose |
|---|---|---|
| Development | `infrastructure/environments/development.env` | Local dev |
| Testing | `infrastructure/environments/testing.env` | CI/test suite |
| Production | `infrastructure/environments/production.env` | Live deployment |

## Configuration Sources (Priority Order)

1. Environment variables (highest)
2. `.env` file in project root
3. `infrastructure/environments/<env>.env` template
4. Application defaults (lowest)

## Production Configuration

See `infrastructure/docs/PRODUCTION_CONFIG.md` for complete configuration reference.

## Verification

After deployment, verify:

```bash
# Health endpoint
curl -s https://app.shunyaos.com/health

# Readiness
curl -s https://app.shunyaos.com/ready

# Liveness
curl -s https://app.shunyaos.com/live

# HTTPS
curl -sI https://app.shunyaos.com/health | grep -i "strict-transport-security"

# Static assets
curl -sI https://app.shunyaos.com/static/css/app.css | grep -i "cache-control"
```