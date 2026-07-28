#!/usr/bin/env bash
# =============================================================================
# SHUNYA — Deterministic Deployment Script
# =============================================================================
# Usage: ./infrastructure/scripts/deploy.sh [environment]
#   environment: production (default), testing, development
#
# Deployment sequence:
#   1. Fetch — pull latest code
#   2. Install — build dependencies
#   3. Migration — run database schema migrations
#   4. Restart — reload application processes
#   5. Verification — confirm health endpoints respond
#   6. Health Check — full runtime verification
# =============================================================================

set -euo pipefail

ENVIRONMENT="${1:-production}"
DEPLOY_DIR="/home/shunya-deploy/shunya_os"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_LOG="/var/log/shunya/deploy-${TIMESTAMP}.log"
BACKUP_DIR="/var/backups/shunya/${TIMESTAMP}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA deployment started: ${ENVIRONMENT}" | tee -a "${DEPLOY_LOG}"

# ---- Environment validation ----
if [[ ! -f "${DEPLOY_DIR}/.env" && "${ENVIRONMENT}" == "production" ]]; then
    echo "ERROR: .env file not found at ${DEPLOY_DIR}/.env" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 1: Fetch ----
echo "[1/6] Fetching latest code..." | tee -a "${DEPLOY_LOG}"
cd "${DEPLOY_DIR}"
git fetch origin main
git checkout main
git pull origin main
echo "  Commit: $(git rev-parse HEAD)" | tee -a "${DEPLOY_LOG}"

# ---- Step 2: Install ----
echo "[2/6] Installing dependencies..." | tee -a "${DEPLOY_LOG}"
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt 2>&1 | tee -a "${DEPLOY_LOG}"

# ---- Step 3: Migration ----
echo "[3/6] Running database migrations..." | tee -a "${DEPLOY_LOG}"
if [ -f "alembic.ini" ]; then
    alembic upgrade head 2>&1 | tee -a "${DEPLOY_LOG}" || echo "  WARNING: Migration may have failed, check logs" | tee -a "${DEPLOY_LOG}"
else
    echo "  SKIP: No alembic.ini found" | tee -a "${DEPLOY_LOG}"
fi

# ---- Step 4: Restart ----
echo "[4/6] Restarting application..." | tee -a "${DEPLOY_LOG}"
if command -v systemctl &> /dev/null; then
    sudo systemctl reload shunya 2>&1 | tee -a "${DEPLOY_LOG}" || \
    sudo systemctl restart shunya 2>&1 | tee -a "${DEPLOY_LOG}"
elif command -v docker-compose &> /dev/null; then
    docker-compose up -d --build --no-deps web 2>&1 | tee -a "${DEPLOY_LOG}"
else
    echo "  WARNING: No known restart mechanism. Reload gunicorn manually."
    echo "  kill -HUP $(cat /var/run/shunya.pid 2>/dev/null || echo '<pid>')"
fi

# ---- Step 5: Verification ----
echo "[5/6] Verifying deployment..." | tee -a "${DEPLOY_LOG}"
sleep 3
HEALTH_URL="http://127.0.0.1:8000/health"
for i in 1 2 3 4 5; do
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        echo "  Application reachable at ${HEALTH_URL}" | tee -a "${DEPLOY_LOG}"
        break
    fi
    echo "  Attempt ${i}/5 — waiting..." | tee -a "${DEPLOY_LOG}"
    sleep 2
done

# ---- Step 6: Health Check ----
echo "[6/6] Running health check..." | tee -a "${DEPLOY_LOG}"
HEALTH_RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || echo '{"status":"unreachable"}')
echo "  Health response: ${HEALTH_RESPONSE}" | tee -a "${DEPLOY_LOG}"

if echo "${HEALTH_RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    echo "  HEALTHY — deployment successful" | tee -a "${DEPLOY_LOG}"
else
    echo "  WARNING: Health check did not return 'ok'. Check logs." | tee -a "${DEPLOY_LOG}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA deployment completed: ${ENVIRONMENT}" | tee -a "${DEPLOY_LOG}"
echo "Log: ${DEPLOY_LOG}"