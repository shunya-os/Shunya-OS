# SHUNYA Recovery Guide

## Recovery Procedures

### Recovery: Failed Deployment

```bash
./infrastructure/scripts/recover.sh deployment
```

**Manual steps:**

1. Check if the previous deployment is still running via `/health`
2. If unreachable, rollback to the previous commit
3. Restart the application
4. Verify health

### Recovery: Migration Failure

```bash
./infrastructure/scripts/recover.sh migration
```

**Manual steps:**

1. Check migration history: `alembic history`
2. Downgrade: `alembic downgrade -1`
3. If auto-downgrade fails, fix the migration script manually
4. Restart the application

### Recovery: Restart Failure

```bash
./infrastructure/scripts/recover.sh restart
```

**Manual steps:**

1. Check for stale PID files: `rm -f gunicorn.pid`
2. Check port conflicts: `ss -tlnp | grep :8000`
3. Force stop: `docker-compose down web`
4. Force start: `docker-compose up -d web`
5. Verify: `curl -s http://127.0.0.1:8000/health`

### Recovery: Complete System Failure

```bash
./infrastructure/scripts/recover.sh complete
```

**Manual steps:**

1. Check Docker: `docker info`
2. Check `.env` exists and has valid secrets
3. Rebuild: `docker-compose up -d --build`
4. Wait for readiness (up to 30 seconds)
5. Verify health: `curl -s http://127.0.0.1:8000/health`

## Recovery Logs

All recovery operations log to `/var/log/shunya/recovery-*.log`.

## Disaster Recovery Checklist

- [ ] Application source code (git)
- [ ] Environment secrets (`.env` backup)
- [ ] Database backups (PostgreSQL dump)
- [ ] SSL certificates (Let's Encrypt)
- [ ] nginx configuration
- [ ] Docker Compose configuration
- [ ] Deployment scripts

## Recovery Verification

After any recovery procedure, verify:

```bash
# 1. Application is running
curl -s http://127.0.0.1:8000/live

# 2. Database is connected
curl -s http://127.0.0.1:8000/ready

# 3. Full health check
curl -s http://127.0.0.1:8000/health

# 4. HTTPS is functional
curl -sI https://app.shunyaos.com/health

# 5. Test suite passes
cd /home/shunya-deploy/shunya_os
source .venv/bin/activate
python -m pytest tests/space/ test_app.py tests/graph/ tests/decision/ tests/evidence/ tests/cortex/ tests/temporal/ --ignore=tests/test_models.py --tb=line
```