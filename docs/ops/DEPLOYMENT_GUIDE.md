# SHUNYA Production Deployment Guide

> **Document Type:** Canonical Deployment Guide  
> **Directive:** FOR-2C.3  
> **Status:** Ratified  
> **Date:** 2026-07-26  

This guide allows any engineer to deploy SHUNYA from a fresh environment using only the repository and documented setup steps.

---

## 1. System Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Ubuntu/Debian | 22.04+ | Host operating system |
| Python | 3.12 | Application runtime |
| PostgreSQL | 16.x | Primary database |
| Redis | 7.x | Session store, rate limiting |
| Nginx | latest | Reverse proxy (production only) |
| wkhtmltopdf | 0.12.6+ | PDF generation |

## 2. Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | Flask session signing key |
| `SECURITY_PASSWORD_SALT` | No | auto | Password hashing salt |
| `REDIS_URL` | No | — | Redis connection (caching, sessions) |
| `STORAGE_PATH` | No | `./storage` | Uploaded file storage root |
| `OPENROUTER_API_KEY` | No | — | AI model access via OpenRouter |
| `OPENAI_API_KEY` | No | — | AI model access via OpenAI |
| `DISABLE_RATE_LIMIT` | No | `0` | Disable rate limiting (dev only) |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `SENTRY_DSN` | No | — | Error tracking |

### Database URL format

```
DATABASE_URL="postgresql://shunya:<password>@localhost:5432/shunya_os"
```

## 3. Server Setup

### 3.1 System Dependencies

```bash
sudo apt update && sudo apt install -y \
    python3.12 python3.12-venv python3.12-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    wkhtmltopdf \
    build-essential libpq-dev
```

### 3.2 PostgreSQL Setup

```bash
# Create database user
sudo -u postgres createuser --superuser shunya

# Create production database
sudo -u postgres createdb shunya_os

# Set password
sudo -u postgres psql -c "ALTER USER shunya WITH PASSWORD '<your-password>';"

# Enable pgvector extension
sudo -u postgres psql -d shunya_os -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3.3 Redis Setup

```bash
sudo systemctl enable redis-server && sudo systemctl start redis-server
```

## 4. Application Installation

### 4.1 Clone Repository

```bash
git clone https://github.com/shunya-os/Shunya-OS.git
cd Shunya-OS
git checkout main  # or master for CI/deploy
```

### 4.2 Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 4.3 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## 5. Database Initialization

### 5.1 Configure Environment

```bash
export DATABASE_URL="postgresql://shunya:<password>@localhost:5432/shunya_os"
export SECRET_KEY="<generate-a-random-64-char-string>"
```

### 5.2 Initialize Schema

The application creates all tables automatically on first startup:

```bash
cd /path/to/shunya_os
source .venv/bin/activate
export DATABASE_URL="..."
export SECRET_KEY="..."

# Option A: Using Flask shell
python3 -c "
from wsgi import app
with app.app_context():
    from app import db
    db.create_all()
    print('Schema created successfully.')
"
```

### 5.3 Run Alembic Migrations (for future schema changes)

```bash
alembic upgrade head
```

### 5.4 Verify Schema

```bash
# Check that core canonical tables exist
python3 -c "
from sqlalchemy import create_engine, text
e = create_engine('$DATABASE_URL')
with e.connect() as conn:
    tables = ['organizations', 'org_members', 'org_invitations', 
              'departments', 'rel_relationships', 'rel_timeline',
              'rel_ai_memory', 'proposals', 'knowledge_documents',
              'auth_roles', 'auth_member_roles']
    for t in tables:
        r = conn.execute(text(f\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{t}')\"))
        exists = r.scalar()
        print(f'  {\"✓\" if exists else \"✗\"} {t}')
"
```

## 6. Application Startup

### 6.1 Development

```bash
cd /path/to/shunya_os
source .venv/bin/activate
export DATABASE_URL="..."
export SECRET_KEY="..."
export DISABLE_RATE_LIMIT=1

python3 app.py
```

### 6.2 Production (Gunicorn)

```bash
cd /path/to/shunya_os
source .venv/bin/activate
export DATABASE_URL="..."
export SECRET_KEY="..."

gunicorn --workers 4 \
    --bind 127.0.0.1:5001 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile /var/log/shunya/access.log \
    --error-logfile /var/log/shunya/error.log \
    wsgi:app
```

### 6.3 Systemd Service

```ini
# /etc/systemd/system/shunya.service
[Unit]
Description=SHUNYA OS
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=shunya-deploy
WorkingDirectory=/home/shunya-deploy/shunya_os
Environment=DATABASE_URL=postgresql://shunya:***@localhost:5432/shunya_os
Environment=SECRET_KEY=***
ExecStart=/home/shunya-deploy/shunya_os/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    --access-logfile /var/log/shunya/access.log \
    --error-logfile /var/log/shunya/error.log \
    wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 7. Verification

### 7.1 Health Check

```bash
curl http://127.0.0.1:5001/health
```

Expected response:
```json
{"database": "connected", "status": "ok", "environment": "production"}
```

### 7.2 Authentication

```bash
curl -X POST http://127.0.0.1:5001/api/v1/founder/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@shunyaos.com","password":"your-password","name":"Admin"}'
```

### 7.3 Organization Creation

```bash
curl -X POST http://127.0.0.1:5001/api/v1/for2/seed \
  -b /path/to/cookies.txt
```

### 7.4 Relationship Creation

```bash
curl -X POST http://127.0.0.1:5001/relationships/api/v1/relationships \
  -b /path/to/cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Test Customer","relationship_type":"customer","email":"test@example.com"}'
```

### 7.5 Proposal Creation

```bash
curl -X POST http://127.0.0.1:5001/api/v1/for1/proposals \
  -b /path/to/cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"lead_id":1,"ai_generate":true,"relationship_id":1}'
```

## 8. Nginx Configuration

```nginx
# /etc/nginx/sites-available/shunya
server {
    listen 80;
    server_name shunyaos.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/shunya-deploy/shunya_os/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/shunya-deploy/shunya_os/media/;
        expires 7d;
    }
}
```

## 9. Rollback Procedure

```bash
# 1. Revert to previous deployment
cd /home/shunya-deploy/shunya_os
git checkout <previous-commit-hash>

# 2. Restart application
sudo systemctl restart shunya

# 3. Verify health
curl http://127.0.0.1:5001/health

# 4. If database migration was applied, revert it
alembic downgrade -1
```

## 10. Upgrade Procedure

```bash
# 1. Pull latest code
cd /home/shunya-deploy/shunya_os
git pull origin main

# 2. Install new dependencies
source .venv/bin/activate
pip install -r requirements.txt

# 3. Apply database migrations
alembic upgrade head

# 4. Restart application
sudo systemctl restart shunya

# 5. Verify
sleep 5
curl http://127.0.0.1:5001/health
```

## 11. Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| 500 on `/health` | Database not accessible | Check `DATABASE_URL` and PostgreSQL status |
| 502 Bad Gateway | Gunicorn not running | Run `sudo systemctl status shunya` |
| Login always fails | `SECRET_KEY` mismatch | Ensure consistent secret across restarts |
| Tables not found | Schema not initialized | Run `db.create_all()` in Flask shell |
| PDF generation fails | Missing wkhtmltopdf | `sudo apt install wkhtmltopdf` |
| AI features fail | No API key configured | Set `OPENROUTER_API_KEY` environment variable |

## 12. Backup Strategy

```bash
# Database backup (daily)
pg_dump shunya_os > /backups/shunya_$(date +%Y%m%d).sql

# File storage backup (daily)
rsync -av /home/shunya-deploy/shunya_os/static/ /backups/static/
rsync -av /home/shunya-deploy/shunya_os/media/ /backups/media/

# Retention: 30 days daily, 12 months monthly
find /backups/ -name "shunya_*.sql" -mtime +30 -delete
```