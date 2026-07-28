# SHUNYA Rollback Guide

## Rollback Scenarios

### Scenario 1: Failed Application Deployment

**Detected by:** Health check returns non-200 after deployment.

**Procedure:**

```bash
# Rollback to previous commit
./infrastructure/scripts/rollback.sh

# Or specify a specific commit
./infrastructure/scripts/rollback.sh <commit_hash>
```

**Manual rollback:**

```bash
cd /home/shunya-deploy/shunya_os

# 1. Record current state
git log --oneline -5

# 2. Reset to previous deployment
git reset --hard HEAD~1

# 3. Reinstall if requirements changed
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# 4. Restart
docker-compose up -d --build web

# 5. Verify
curl -s http://127.0.0.1:8000/health
```

### Scenario 2: Migration Failure

**Detected by:** `alembic upgrade head` fails during deployment.

**Procedure:**

```bash
cd /home/shunya-deploy/shunya_os

# 1. Downgrade one step
alembic downgrade -1

# 2. Check migration history
alembic history

# 3. Restart with pre-migration code
git reset --hard HEAD~1
docker-compose up -d --build web

# 4. Fix migration script, then re-deploy
```

### Scenario 3: Configuration Error

**Detected by:** Application starts but fails to serve requests.

**Procedure:**

```bash
# 1. Restore previous .env
cp /var/backups/shunya/.env.$(date -d yesterday +%Y%m%d) .env

# 2. Restart
docker-compose restart web

# 3. Verify
curl -s http://127.0.0.1:8000/health
```

## Rollback Verification

After any rollback, confirm:

```bash
# 1. Correct commit is deployed
git rev-parse HEAD

# 2. Application is healthy
curl -s http://127.0.0.1:8000/health

# 3. Database is connected
curl -s http://127.0.0.1:8000/ready

# 4. Tests pass
source .venv/bin/activate
python -m pytest tests/space/ test_app.py tests/graph/ tests/decision/ tests/evidence/ tests/cortex/ tests/temporal/ --ignore=tests/test_models.py --tb=line
```

## Rollback Log

Rollback logs are stored at `/var/log/shunya/rollback-*.log`.