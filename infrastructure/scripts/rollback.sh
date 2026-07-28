#!/usr/bin/env bash
# =============================================================================
# SHUNYA — Rollback Script
# =============================================================================
# Usage: ./infrastructure/scripts/rollback.sh [commit_hash]
#
# Restores the previous deployment by reverting to the specified commit
# or the previous deployment snapshot.
# =============================================================================

set -euo pipefail

COMMIT_HASH="${1:-}"
DEPLOY_DIR="/home/shunya-deploy/shunya_os"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ROLLBACK_LOG="/var/log/shunya/rollback-${TIMESTAMP}.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA rollback started" | tee -a "${ROLLBACK_LOG}"

cd "${DEPLOY_DIR}"

# Determine target commit
if [ -z "${COMMIT_HASH}" ]; then
    # Rollback to previous commit (one before HEAD)
    COMMIT_HASH=$(git rev-parse HEAD~1 2>/dev/null || echo "")
    if [ -z "${COMMIT_HASH}" ]; then
        echo "ERROR: No previous commit found. Specify a commit hash." | tee -a "${ROLLBACK_LOG}"
        exit 1
    fi
    echo "Rolling back to previous commit: ${COMMIT_HASH}" | tee -a "${ROLLBACK_LOG}"
else
    echo "Rolling back to specified commit: ${COMMIT_HASH}" | tee -a "${ROLLBACK_LOG}"
fi

# Record current state before rollback
echo "Current commit: $(git rev-parse HEAD)" | tee -a "${ROLLBACK_LOG}"
echo "Current branch: $(git rev-parse --abbrev-ref HEAD)" | tee -a "${ROLLBACK_LOG}"

# Hard reset to target commit
git reset --hard "${COMMIT_HASH}" 2>&1 | tee -a "${ROLLBACK_LOG}"

# Reinstall dependencies if requirements.txt changed
if git diff HEAD~1 --name-only 2>/dev/null | grep -q "requirements.txt"; then
    echo "Requirements changed — reinstalling dependencies..." | tee -a "${ROLLBACK_LOG}"
    source .venv/bin/activate
    pip install --no-cache-dir -r requirements.txt 2>&1 | tee -a "${ROLLBACK_LOG}"
fi

# Run any rollback migrations if needed
if [ -f "alembic.ini" ]; then
    echo "Checking for rollback migration..." | tee -a "${ROLLBACK_LOG}"
    # Attempt downgrade one step
    alembic downgrade -1 2>&1 | tee -a "${ROLLBACK_LOG}" || echo "  No rollback migration needed" | tee -a "${ROLLBACK_LOG}"
fi

# Restart application
echo "Restarting application..." | tee -a "${ROLLBACK_LOG}"
if command -v systemctl &> /dev/null; then
    sudo systemctl restart shunya 2>&1 | tee -a "${ROLLBACK_LOG}"
elif command -v docker-compose &> /dev/null; then
    docker-compose up -d --build web 2>&1 | tee -a "${ROLLBACK_LOG}"
fi

# Verify
sleep 3
HEALTH_URL="http://127.0.0.1:8000/health"
HEALTH_RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || echo '{"status":"unreachable"}')
echo "Post-rollback health: ${HEALTH_RESPONSE}" | tee -a "${ROLLBACK_LOG}"

if echo "${HEALTH_RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    echo "ROLLBACK COMPLETE — application healthy" | tee -a "${ROLLBACK_LOG}"
else
    echo "ROLLBACK COMPLETE — application may be degraded. Check logs." | tee -a "${ROLLBACK_LOG}"
fi

echo "Commit: $(git rev-parse HEAD)" | tee -a "${ROLLBACK_LOG}"
echo "Log: ${ROLLBACK_LOG}"