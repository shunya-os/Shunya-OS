# SHUNYA Verification Framework

## Repository State

```bash
cd /home/shunya-deploy/shunya_os
git status
```

Expected: Working tree clean, no uncommitted changes.

## Canonical Verification Command

```bash
cd /home/shunya-deploy/shunya_os
source .venv/bin/activate
python -m pytest tests/space/ test_app.py tests/graph/ tests/decision/ tests/evidence/ tests/cortex/ tests/temporal/ --ignore=tests/test_models.py --tb=line
```

## Expected Verification Result

```
816 passed, 29 warnings, 0 failures
```

## Deployment Verification

### Health Endpoints

```bash
# Full health check
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
# Expected: {"status": "ok", "database": "connected", "uptime_seconds": N, ...}

# Readiness probe
curl -s http://127.0.0.1:8000/ready | python3 -m json.tool
# Expected: {"status": "ok", "service": "shunya", "database": "ready"}

# Liveness probe
curl -s http://127.0.0.1:8000/live | python3 -m json.tool
# Expected: {"status": "alive", "service": "shunya"}
```

### HTTPS Verification

```bash
# HTTPS is functional
curl -sI https://app.shunyaos.com/health | head -5
# Expected: 200 OK

# HSTS header is present
curl -sI https://app.shunyaos.com/health | grep -i "strict-transport-security"
# Expected: Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

# HTTP redirects to HTTPS
curl -sI http://app.shunyaos.com/health | head -5
# Expected: 301 Moved Permanently → Location: https://app.shunyaos.com/health
```

### Static Assets Verification

```bash
# Immutable cache header
curl -sI https://app.shunyaos.com/static/css/app.css | grep -i "cache-control"
# Expected: Cache-Control: public, immutable, max-age=31536000
```

## Rollback Verification

```bash
# 1. Verify correct commit
cd /home/shunya-deploy/shunya_os
git rev-parse HEAD

# 2. Verify application is healthy
curl -s http://127.0.0.1:8000/health | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)"

# 3. Verify database is connected
curl -s http://127.0.0.1:8000/ready | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('database')=='ready' else 1)"

# 4. Run test suite
source .venv/bin/activate
python -m pytest tests/space/ test_app.py tests/graph/ tests/decision/ tests/evidence/ tests/cortex/ tests/temporal/ --ignore=tests/test_models.py --tb=line
```

## Recovery Verification

After any recovery procedure, run:

```bash
# Step 1: Liveness
curl -s http://127.0.0.1:8000/live
# Expected: {"status": "alive"}

# Step 2: Readiness
curl -s http://127.0.0.1:8000/ready
# Expected: {"status": "ok", "database": "ready"}

# Step 3: Full health
curl -s http://127.0.0.1:8000/health
# Expected: {"status": "ok"}

# Step 4: Test suite
cd /home/shunya-deploy/shunya_os
source .venv/bin/activate
python -m pytest tests/space/ test_app.py tests/graph/ tests/decision/ tests/evidence/ tests/cortex/ tests/temporal/ --ignore=tests/test_models.py --tb=line
# Expected: 816 passed, 0 failures
```