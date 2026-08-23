#!/usr/bin/env bash
# =============================================================================
# SHUNYA — Deterministic Deployment Script
# =============================================================================
# Usage: ./infrastructure/scripts/deploy.sh [environment] [target_sha]
#   environment: production (default), testing, development
#   target_sha:  exact commit SHA to deploy (optional; defaults to remote master)
#
# Deployment sequence:
#   1. Verify repository
#   2. Fetch canonical remote
#   3. Checkout exact certified SHA
#   4. Verify clean intended state
#   5. Install deterministic dependencies
#   6. Build frontend
#   7. Run migration check (with backup)
#   8. Apply migration
#   9. Restart service via systemctl (canonical process manager)
#  10. Readiness check
#  11. Health check
#  12. Smoke test
# =============================================================================

set -euo pipefail

ENVIRONMENT="${1:-production}"
TARGET_SHA="${2:-}"

DEPLOY_DIR="/home/shunya-deploy/shunya_os"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_LOG="/var/log/shunya/deploy-${TIMESTAMP}.log"
BACKUP_DIR="/var/backups/shunya/${TIMESTAMP}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA deployment started: ${ENVIRONMENT}" | tee -a "${DEPLOY_LOG}"

# ---- Validate target SHA format ----
if [[ -n "${TARGET_SHA}" ]]; then
    if ! [[ "${TARGET_SHA}" =~ ^[0-9a-f]{40}$ ]]; then
        echo "ERROR: Invalid target SHA format: ${TARGET_SHA}" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
fi

# ---- Environment validation ----
if [[ ! -f "${DEPLOY_DIR}/.env" && "${ENVIRONMENT}" == "production" ]]; then
    echo "ERROR: .env file not found at ${DEPLOY_DIR}/.env" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 1: Verify repository ----
echo "[1/12] Verifying repository..." | tee -a "${DEPLOY_LOG}"
cd "${DEPLOY_DIR}"
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "ERROR: Not a git repository at ${DEPLOY_DIR}" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# Record previous deployed SHA for rollback
PREVIOUS_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
echo "  Previous SHA: ${PREVIOUS_SHA}" | tee -a "${DEPLOY_LOG}"

# ---- Step 2: Fetch canonical remote ----
echo "[2/12] Fetching canonical remote..." | tee -a "${DEPLOY_LOG}"
if ! git fetch origin master 2>&1 | tee -a "${DEPLOY_LOG}"; then
    echo "ERROR: git fetch failed — cannot reach remote repository" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 3: Checkout exact certified SHA ----
if [[ -n "${TARGET_SHA}" ]]; then
    echo "[3/12] Checking out exact certified SHA: ${TARGET_SHA}" | tee -a "${DEPLOY_LOG}"
    if ! git checkout "${TARGET_SHA}" 2>&1 | tee -a "${DEPLOY_LOG}"; then
        echo "ERROR: Failed to checkout SHA ${TARGET_SHA} — SHA may not exist in repository" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
else
    echo "[3/12] No target SHA provided — using remote master head" | tee -a "${DEPLOY_LOG}"
    git checkout master 2>&1 | tee -a "${DEPLOY_LOG}"
    git reset --hard origin/master 2>&1 | tee -a "${DEPLOY_LOG}"
fi

DEPLOYED_SHA=$(git rev-parse HEAD)
echo "  Deployed SHA: ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"

# Verify target SHA matches deployed SHA when target was provided
if [[ -n "${TARGET_SHA}" && "${DEPLOYED_SHA}" != "${TARGET_SHA}" ]]; then
    echo "ERROR: Deployed SHA (${DEPLOYED_SHA}) does not match target SHA (${TARGET_SHA})" | tee -a "${DEPLOY_LOG}"
    echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 4: Verify clean intended state ----
echo "[4/12] Verifying working tree..." | tee -a "${DEPLOY_LOG}"
if [[ -n "$(git status --porcelain)" ]]; then
    echo "WARNING: Working tree not clean after checkout:" | tee -a "${DEPLOY_LOG}"
    git status --porcelain | tee -a "${DEPLOY_LOG}"
    echo "ERROR: Deploying from a dirty working tree is not allowed" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 5: Install deterministic dependencies ----
echo "[5/12] Installing dependencies..." | tee -a "${DEPLOY_LOG}"
source .venv/bin/activate
if ! pip install --no-cache-dir -r requirements.txt 2>&1 | tee -a "${DEPLOY_LOG}"; then
    echo "ERROR: Dependency installation failed" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 6: Build frontend ----
echo "[6/12] Building frontend..." | tee -a "${DEPLOY_LOG}"
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    (
        cd frontend
        if ! npm install --legacy-peer-deps 2>&1 | tee -a "${DEPLOY_LOG}"; then
            echo "ERROR: Frontend dependency install failed" | tee -a "${DEPLOY_LOG}"
            exit 1
        fi
        if ! npm run build 2>&1 | tee -a "${DEPLOY_LOG}"; then
            echo "ERROR: Frontend build failed" | tee -a "${DEPLOY_LOG}"
            exit 1
        fi
    )
else
    echo "  SKIP: No frontend directory found" | tee -a "${DEPLOY_LOG}"
fi

# ---- Step 7: Migration check + backup ----
echo "[7/12] Checking migrations..." | tee -a "${DEPLOY_LOG}"
if [ -f "alembic.ini" ]; then
    CURRENT_REV=$(alembic current 2>/dev/null | head -1 || echo "unknown")
    echo "  Current migration: ${CURRENT_REV}" | tee -a "${DEPLOY_LOG}"
    HEAD_REV=$(alembic heads 2>/dev/null | head -1 || echo "unknown")
    echo "  Head migration: ${HEAD_REV}" | tee -a "${DEPLOY_LOG}"
    if [ "${CURRENT_REV}" != "${HEAD_REV}" ]; then
        echo "  Migration required. Backing up database first..." | tee -a "${DEPLOY_LOG}"
        mkdir -p "${BACKUP_DIR}"
        if command -v pg_dump &> /dev/null; then
            source .env 2>/dev/null || true
            pg_dump "postgresql://shunya:***@localhost:5432/shunya_os" \
                > "${BACKUP_DIR}/predeploy.sql.gz" 2>/dev/null || \
                pg_dump postgresql://shunya@localhost:5432/shunya_os \
                | gzip > "${BACKUP_DIR}/predeploy.sql.gz" 2>/dev/null || \
                echo "  WARNING: pg_dump backup failed (continuing)" | tee -a "${DEPLOY_LOG}"
        fi
    fi
else
    echo "  SKIP: No alembic.ini found" | tee -a "${DEPLOY_LOG}"
fi

# ---- Step 8: Apply migration ----
echo "[8/12] Applying migrations..." | tee -a "${DEPLOY_LOG}"
if [ -f "alembic.ini" ]; then
    if ! alembic upgrade head 2>&1 | tee -a "${DEPLOY_LOG}"; then
        echo "ERROR: Migration failed" | tee -a "${DEPLOY_LOG}"
        echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
    echo "  Migrations applied successfully" | tee -a "${DEPLOY_LOG}"
else
    echo "  SKIP: No alembic.ini found" | tee -a "${DEPLOY_LOG}"
fi

# ---- Step 9: Restart service (canonical path: systemctl) ----
echo "[9/12] Restarting application via systemctl..." | tee -a "${DEPLOY_LOG}"
# The canonical production process manager is systemd. shunya-deploy has NOPASSWD
# sudo for systemctl restart/stop/start/status shunya (configured via sudoers).
if command -v systemctl &> /dev/null; then
    if sudo -n systemctl restart shunya 2>&1 | tee -a "${DEPLOY_LOG}"; then
        echo "  Restart via systemctl succeeded" | tee -a "${DEPLOY_LOG}"
    else
        echo "ERROR: systemctl restart shunya failed." | tee -a "${DEPLOY_LOG}"
        echo "  Check: sudoers entry for shunya-deploy (systemctl NOPASSWD)" | tee -a "${DEPLOY_LOG}"
        echo "  Check: systemctl status shunya for error details" | tee -a "${DEPLOY_LOG}"
        echo "ROLLBACK: checkout ${PREVIOUS_SHA} and run: sudo systemctl restart shunya" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
elif command -v docker-compose &> /dev/null; then
    docker-compose up -d --build --no-deps web 2>&1 | tee -a "${DEPLOY_LOG}"
else
    echo "ERROR: No known production process manager (systemctl not found)" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 10: Readiness check ----
echo "[10/12] Waiting for readiness..." | tee -a "${DEPLOY_LOG}"
sleep 3
HEALTH_URL="${SHUNYA_HEALTH_URL:-http://127.0.0.1:5001/health}"
for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        echo "  Application reachable at ${HEALTH_URL}" | tee -a "${DEPLOY_LOG}"
        break
    fi
    if [ "$i" -eq 10 ]; then
        echo "ERROR: Application not reachable after 10 attempts" | tee -a "${DEPLOY_LOG}"
        echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
    echo "  Attempt ${i}/10 — waiting..." | tee -a "${DEPLOY_LOG}"
    sleep 3
done

# ---- Step 11: Health check ----
echo "[11/12] Running health check..." | tee -a "${DEPLOY_LOG}"
HEALTH_RESPONSE=$(curl -sf "${HEALTH_URL}" 2>/dev/null || echo '{"status":"unreachable"}')
echo "  Health response: ${HEALTH_RESPONSE}" | tee -a "${DEPLOY_LOG}"

if echo "${HEALTH_RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
    echo "  HEALTHY — deployment successful" | tee -a "${DEPLOY_LOG}"
else
    echo "ERROR: Health check did not return 'ok'." | tee -a "${DEPLOY_LOG}"
    echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 12: Smoke test ----
echo "[12/12] Running smoke test..." | tee -a "${DEPLOY_LOG}"
GIT_COMMIT_IN_HEALTH=$(echo "${HEALTH_RESPONSE}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('git_commit',''))" 2>/dev/null || echo "")
if [ -n "${GIT_COMMIT_IN_HEALTH}" ] && [ "${GIT_COMMIT_IN_HEALTH}" != "${DEPLOYED_SHA}" ]; then
    echo "ERROR: Deployed build mismatch. Health reports ${GIT_COMMIT_IN_HEALTH}, repo at ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"
    echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
    exit 1
fi
echo "  Build provenance verified: ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"
echo "  Smoke test PASSED" | tee -a "${DEPLOY_LOG}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA deployment completed: ${ENVIRONMENT}" | tee -a "${DEPLOY_LOG}"
echo "Log: ${DEPLOY_LOG}"
echo "Previous SHA (rollback): ${PREVIOUS_SHA}"
echo "Deployed SHA: ${DEPLOYED_SHA}"