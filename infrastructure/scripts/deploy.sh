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
BACKUP_DIR="/home/shunya-deploy/backups/shunya/${TIMESTAMP}"

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

# ---- Step 2b: PRESERVE UNCOMMITTED WORK (fail closed) ----
# A deploy must never destroy a developer's uncommitted work. Step 3 used to
# hard-reset the live worktree BEFORE any check, silently discarding local
# commits and edits. The guard below runs FIRST and fails closed on a dirty or
# unexpected tree — nothing is modified when it refuses.
echo "[2/12] Verifying the deploy tree is clean before any checkout..." | tee -a "${DEPLOY_LOG}"
PREFLIGHT_SCRIPT="infrastructure/scripts/deploy_preflight.sh"
if [[ ! -f "${PREFLIGHT_SCRIPT}" ]]; then
    echo "ERROR: ${PREFLIGHT_SCRIPT} is missing — refusing to deploy (expected state)." | tee -a "${DEPLOY_LOG}"
    exit 1
fi
if ! bash "${PREFLIGHT_SCRIPT}" "$(pwd)" 2>&1 | tee -a "${DEPLOY_LOG}"; then
    echo "ERROR: Deploy pre-flight refused this deployment. No work was destroyed." | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 3: Checkout exact certified SHA ----
if [[ -n "${TARGET_SHA}" ]]; then
    echo "[3/12] Checking out exact certified SHA: ${TARGET_SHA}" | tee -a "${DEPLOY_LOG}"
    REMOTE_HEAD=$(git rev-parse origin/master 2>/dev/null || echo "")
    if [[ -n "${REMOTE_HEAD}" && "${TARGET_SHA}" == "${REMOTE_HEAD}" ]]; then
        # Normal CI case: the certified SHA IS the branch head. Check out the
        # BRANCH and hard-reset to it, so HEAD never detaches — not even
        # temporarily. A detached window (however brief) is what allowed a
        # commit made during a deploy to land off-branch and be lost.
        if ! { git checkout master && git reset --hard "${TARGET_SHA}"; } 2>&1 | tee -a "${DEPLOY_LOG}"; then
            echo "ERROR: Failed to check out master at ${TARGET_SHA}" | tee -a "${DEPLOY_LOG}"
            exit 1
        fi
    else
        # Deliberately deploying a non-head SHA: HEAD must be detached so the
        # branch is not moved. Step 14 leaves it that way, with a note.
        if ! git checkout "${TARGET_SHA}" 2>&1 | tee -a "${DEPLOY_LOG}"; then
            echo "ERROR: Failed to checkout SHA ${TARGET_SHA} — SHA may not exist in repository" | tee -a "${DEPLOY_LOG}"
            exit 1
        fi
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
        if ! npm ci 2>&1 | tee -a "${DEPLOY_LOG}"; then
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

# ---- Step 6b: Publish an IMMUTABLE frontend release ----
# Release integrity: production must NOT serve frontend assets from this
# mutable checkout. The build is published to a per-SHA release directory and
# the 'current' symlink is swapped ATOMICALLY, so a local `npm run build` can
# never change what production serves, and the served artifact is always tied
# to a certified SHA.
if [ -d "frontend/dist" ]; then
    RELEASES_ROOT="${SHUNYA_RELEASES_ROOT:-$(cd .. && pwd)/releases}"
    RELEASE_DIR="${RELEASES_ROOT}/${DEPLOYED_SHA}"
    RELEASE_TMP="${RELEASE_DIR}.tmp.$$"
    echo "[6/12] Publishing immutable frontend release -> ${RELEASE_DIR}" | tee -a "${DEPLOY_LOG}"
    rm -rf "${RELEASE_TMP}"
    mkdir -p "${RELEASE_TMP}"
    if ! cp -a frontend/dist/. "${RELEASE_TMP}/"; then
        echo "ERROR: Could not stage the frontend release" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
    ASSET_MANIFEST_SHA=$(find "${RELEASE_TMP}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
    if [[ -z "${ASSET_MANIFEST_SHA}" ]]; then
        echo "ERROR: Could not compute the release asset manifest hash" | tee -a "${DEPLOY_LOG}"
        exit 1
    fi
    cat > "${RELEASE_TMP}/release.json" <<EOF
{"release_sha": "${DEPLOYED_SHA}", "asset_manifest_sha256": "${ASSET_MANIFEST_SHA}", "published_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "publisher": "deploy.sh"}
EOF
    rm -rf "${RELEASE_DIR}"
    mv "${RELEASE_TMP}" "${RELEASE_DIR}"
    # Atomic symlink swap — readers never observe a missing/partial release.
    ln -sfn "${RELEASE_DIR}" "${RELEASES_ROOT}/.current.tmp"
    mv -Tf "${RELEASES_ROOT}/.current.tmp" "${RELEASES_ROOT}/current"
    echo "  Frontend release published (sha=${DEPLOYED_SHA:0:12}, manifest=${ASSET_MANIFEST_SHA:0:12})" | tee -a "${DEPLOY_LOG}"
else
    echo "  SKIP: no frontend/dist to publish" | tee -a "${DEPLOY_LOG}"
fi

# ---- Step 6c: Publish the IMMUTABLE BUILD IDENTITY ----
# Written BEFORE the service restart so the workers that come up in step 9
# already see this deployment's identity. /health reports it as
# backend_release_sha and marks the runtime degraded if the loaded build does
# not match it — so a worker recycling after an un-deployed checkout change is
# reported truthfully instead of appearing certified.
RUNTIME_DATA_ROOT="${RUNTIME_DATA_ROOT:-${HOME}/shunya_data}"
mkdir -p "${RUNTIME_DATA_ROOT}"
BUILD_IDENTITY_FILE="${RUNTIME_DATA_ROOT}/build_identity.json"
cat > "${BUILD_IDENTITY_FILE}" <<IDENTITY
{"backend_release_sha": "${DEPLOYED_SHA}", "build_id": "${DEPLOYED_SHA:0:7}", "deployed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "frontend_release_sha": "${DEPLOYED_SHA}", "frontend_asset_manifest_sha256": "${ASSET_MANIFEST_SHA:-}"}
IDENTITY
echo "[6/12] Build identity published -> ${BUILD_IDENTITY_FILE}" | tee -a "${DEPLOY_LOG}"

# ---- Step 7: Migration check + backup ----
echo "[7/12] Checking migrations..." | tee -a "${DEPLOY_LOG}"
if [ -f "alembic.ini" ]; then
    CURRENT_REV=$(alembic current)
    HEAD_REV=$(alembic heads)
    echo "  Current migration: ${CURRENT_REV}" | tee -a "${DEPLOY_LOG}"
    echo "  Head migration: ${HEAD_REV}" | tee -a "${DEPLOY_LOG}"
    # Always back up before invoking upgrade; no migration after failed backup.
    mkdir -p "${BACKUP_DIR}"
    python3 infrastructure/scripts/backup_database.py "${BACKUP_DIR}/predeploy.dump" 2>&1 | tee -a "${DEPLOY_LOG}"
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
HEALTH_FILE=$(mktemp)
trap 'rm -f "${HEALTH_FILE}"' EXIT
curl --fail --silent --show-error --max-time 30 "${HEALTH_URL}" --output "${HEALTH_FILE}"

if python3 -c "import sys,json; d=json.load(open(sys.argv[1])); sys.exit(0 if d.get('status')=='ok' else 1)" "${HEALTH_FILE}"; then
    echo "  HEALTHY — deployment successful" | tee -a "${DEPLOY_LOG}"
else
    echo "ERROR: Health check did not return 'ok'." | tee -a "${DEPLOY_LOG}"
    echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
    exit 1
fi

# ---- Step 12: Smoke test ----
echo "[12/12] Running smoke test..." | tee -a "${DEPLOY_LOG}"
GIT_COMMIT_IN_HEALTH=$(python3 -c "import sys,json; print(json.load(open(sys.argv[1])).get('git_commit',''))" "${HEALTH_FILE}")
if [ "${GIT_COMMIT_IN_HEALTH}" != "${DEPLOYED_SHA}" ]; then
    echo "ERROR: Deployed build mismatch. Health reports ${GIT_COMMIT_IN_HEALTH}, repo at ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"
    echo "ROLLBACK: checkout ${PREVIOUS_SHA} and restart to roll back" | tee -a "${DEPLOY_LOG}"
    exit 1
fi
echo "  Build provenance verified: ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"
echo "  Smoke test PASSED" | tee -a "${DEPLOY_LOG}"

# ---- Step 13: Record deployment provenance in immutable audit file ----
echo "[13/12] Recording deployment provenance..." | tee -a "${DEPLOY_LOG}"
RUNTIME_DATA_ROOT="${RUNTIME_DATA_ROOT:-${HOME}/shunya_data}"
.venv/bin/python3 -c "
import os; os.environ['RUNTIME_DATA_ROOT'] = '${RUNTIME_DATA_ROOT}'
from app.release_governance import record_normal_deployment
r = record_normal_deployment('${DEPLOYED_SHA}', previous_sha='${PREVIOUS_SHA}')
print(f'  Release type: {r[\"release_type\"]}')
print(f'  Git commit: {r[\"git_commit\"]}')
" 2>&1 | tee -a "${DEPLOY_LOG}"

# ---- Step 14: Re-attach HEAD to the branch ----
# `git checkout <sha>` (Step 3) leaves the repository on a DETACHED HEAD, and
# nothing ever returned it to the branch. Any commit made on this box after a
# deploy would therefore not belong to master and would be silently discarded
# (a `git push origin master` would be a no-op without any error). When the
# deployed SHA IS the remote master head — the normal CI case — reattach HEAD
# to the master branch. The working tree content is identical, so the deployed
# build is unchanged.
REMOTE_MASTER_SHA=$(git rev-parse origin/master 2>/dev/null || echo "")
if [[ -n "${REMOTE_MASTER_SHA}" && "${DEPLOYED_SHA}" == "${REMOTE_MASTER_SHA}" ]]; then
    git checkout master 2>&1 | tee -a "${DEPLOY_LOG}"
    echo "  HEAD re-attached to branch master at ${DEPLOYED_SHA}" | tee -a "${DEPLOY_LOG}"
else
    echo "  NOTE: deployed SHA ${DEPLOYED_SHA} != origin/master ${REMOTE_MASTER_SHA}" | tee -a "${DEPLOY_LOG}"
    echo "  NOTE: leaving a detached HEAD (deploying a non-head SHA is intentional)" | tee -a "${DEPLOY_LOG}"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA deployment completed: ${ENVIRONMENT}" | tee -a "${DEPLOY_LOG}"
echo "Log: ${DEPLOY_LOG}"
echo "Previous SHA (rollback): ${PREVIOUS_SHA}"
echo "Deployed SHA: ${DEPLOYED_SHA}"