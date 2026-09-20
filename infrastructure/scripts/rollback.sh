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

# Refuse to destroy uncommitted work. A rollback that silently discards a
# developer's edits is not a recovery — it is the same defect the deploy path
# already guards against, so the identical fail-closed guard is used here.
PREFLIGHT="infrastructure/scripts/deploy_preflight.sh"
if [ -f "${PREFLIGHT}" ]; then
    if ! bash "${PREFLIGHT}" "$(pwd)" 2>&1 | tee -a "${ROLLBACK_LOG}"; then
        echo "ERROR: refusing to roll back across a dirty tree. Commit, stash or discard deliberately." | tee -a "${ROLLBACK_LOG}"
        exit 1
    fi
fi

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
# Production serves on 127.0.0.1:5001. The previous 8000 was a stale docker-era
# port, so this check reported "unreachable" even on a healthy system — and the
# rollback was declared complete either way. Both are fixed: the correct port is
# checked, and an unhealthy result is a hard failure.
sleep 3
HEALTH_URL="${SHUNYA_HEALTH_URL:-http://127.0.0.1:5001/health}"
HEALTH_FILE=$(mktemp)
trap 'rm -f "${HEALTH_FILE}"' EXIT

# Network output is never piped into an interpreter: the response is written to
# a file and inspected with grep.
if curl -sf --max-time 15 -o "${HEALTH_FILE}" "${HEALTH_URL}" \
        && grep -q '"status":"ok"' "${HEALTH_FILE}"; then
    echo "ROLLBACK COMPLETE — application healthy" | tee -a "${ROLLBACK_LOG}"
else
    echo "ROLLBACK FAILED — application is NOT healthy at ${HEALTH_URL}" | tee -a "${ROLLBACK_LOG}"
    echo "Commit: $(git rev-parse HEAD)" | tee -a "${ROLLBACK_LOG}"
    echo "Log: ${ROLLBACK_LOG}"
    exit 1
fi

echo "Commit: $(git rev-parse HEAD)" | tee -a "${ROLLBACK_LOG}"
echo "Log: ${ROLLBACK_LOG}"