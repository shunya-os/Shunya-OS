# SHUNYA Production Environment

**Status:** LIVE
**Environment:** Production
**Created:** 2026-07-16
**Production Tag:** v0.1.0-production

---

# Production URL

https://shunyaos.com

Health Endpoint

https://shunyaos.com/health

Expected Response

{
  "status": "ok",
  "database": "connected"
}

---

# Infrastructure

Provider:
Contabo VPS

Operating System:
Ubuntu

Web Server:
NGINX

Application Server:
Gunicorn

Application:
Flask (SHUNYA)

Database:
PostgreSQL

Process Manager:
systemd

SSL:
HTTPS enabled

---

# Repository

Repository:
git@github.com:shunya-os/Shunya-OS.git

Production Branch:
master

Production Tag:
v0.1.0-production

Current Production Commit:

d49dc5b537b8532ceedae0c6b85cd4eb05d3dc00

---

# Production Service

Service Name:

shunya.service

Check Status

systemctl status shunya.service

Restart

systemctl restart shunya.service

Stop

systemctl stop shunya.service

Start

systemctl start shunya.service

Reload systemd

systemctl daemon-reload

---

# NGINX

Configuration

/etc/nginx/sites-available/shunya

Enabled Site

/etc/nginx/sites-enabled/shunya

Test Configuration

nginx -t

Reload

systemctl reload nginx

Restart

systemctl restart nginx

---

# Health Verification

Application

curl https://shunyaos.com/health

Internal

curl http://127.0.0.1:5001/health

---

# Deployment

Login

ssh root@217.76.53.46

Repository

cd /home/shunya-deploy/shunya_os

Switch User

sudo -u shunya-deploy bash

Pull Latest

git pull

Restart

exit

systemctl restart shunya.service

Verify

systemctl status shunya.service

curl https://shunyaos.com/health

---

# Logs

Application

journalctl -u shunya.service -f

Gunicorn

tail -f /var/log/shunya/error.log

NGINX

tail -f /var/log/nginx/error.log

---

# Backup

Configuration Files

/etc/systemd/system/shunya.service

/etc/nginx/sites-available/shunya

Environment

/home/shunya-deploy/shunya_os/.env

Snapshot

Contabo VPS Snapshot

---

# Recovery Checklist

1. Restore VPS snapshot if required.
2. Verify PostgreSQL is running.
3. Verify shunya.service is active.
4. Verify NGINX configuration.
5. Verify HTTPS.
6. Verify health endpoint.
7. Verify database connectivity.

---

# Production Rules

- Never edit production directly without Git.
- Test locally before deployment.
- Always tag production releases.
- Always verify /health after deployment.
- Take a VPS snapshot before major upgrades.
- Keep .env out of Git.
- Never commit secrets.

---

# Release History

## v0.1.0-production

Date:
2026-07-16

Summary:
- First successful production deployment
- HTTPS enabled
- NGINX configured
- systemd service operational
- PostgreSQL connected
- Health endpoint operational
- Production baseline established
