#!/usr/bin/env bash
# =============================================================================
# SHUNYA — Recovery Script
# =============================================================================
# Usage: ./infrastructure/scripts/recover.sh [scenario]
#   Scenarios: deployment, migration, restart, complete
#
# Recovery procedures after:
#   - Failed deployment
#   - Migration failure
#   - Restart failure
#   - Complete system failure
# =============================================================================

set -euo pipefail

SCENARIO="${1:-complete}"
DEPLOY_DIR="/home/shunya-deploy/shunya_os"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RECOVERY_LOG="/var/log/shunya/recovery-${TIMESTAMP}.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA recovery started: ${SCENARIO}" | tee -a "${RECOVERY_LOG}"

cd "${DEPLOY_DIR}"

# =============================================================================
# Shared recovery functions
# =============================================================================

_health_check() {
    curl -sf "http://127.0.0.1:8000/health" 2>/dev/null || echo "unreachable"
}

_restart_app() {
    if command -v systemctl &> /dev/null; then
        sudo systemctl restart shunya 2>&1 || true
    elif command -v docker-compose &> /dev/null; then
        docker-compose restart web 2>&1 || docker-compose up -d web 2>&1 || true
    fi
}

# =============================================================================
# Recovery: Failed deployment
# =============================================================================

_recover_deployment() {
    echo "[RECOVERY] Deployment failure detected" | tee -a "${RECOVERY_LOG}"

    # Check if application is running
    HEALTH=$(_health_check)
    if [ "${HEALTH}" != "unreachable" ]; then
        echo "  Previous deployment is still running" | tee -a "${RECOVERY_LOG}"
        return 0
    fi

    # Rollback to previous commit
    echo "  Previous deployment not responding — rolling back" | tee -a "${RECOVERY_LOG}"
    git reset --hard HEAD~1 2>&1 | tee -a "${RECOVERY_LOG}"
    _restart_app
    sleep 5

    # Verify
    HEALTH=$(_health_check)
    if [ "${HEALTH}" != "unreachable" ]; then
        echo "  Rollback successful — application restored" | tee -a "${RECOVERY_LOG}"
    else
        echo "  CRITICAL: Rollback also failed — manual intervention required" | tee -a "${RECOVERY_LOG}"
        return 1
    fi
}

# =============================================================================
# Recovery: Migration failure
# =============================================================================

_recover_migration() {
    echo "[RECOVERY] Migration failure detected" | tee -a "${RECOVERY_LOG}"

    if [ -f "alembic.ini" ]; then
        # Try downgrading one step
        echo "  Attempting migration rollback..." | tee -a "${RECOVERY_LOG}"
        alembic downgrade -1 2>&1 | tee -a "${RECOVERY_LOG}" || {
            echo "  WARNING: Auto-downgrade failed. Manual migration fix required." | tee -a "${RECOVERY_LOG}"
            echo "  Steps:" | tee -a "${RECOVERY_LOG}"
            echo "    1. alembic history" | tee -a "${RECOVERY_LOG}"
            echo "    2. alembic downgrade <previous_revision>" | tee -a "${RECOVERY_LOG}"
            echo "    3. python scripts/migration_repair.py (if available)" | tee -a "${RECOVERY_LOG}"
        }
    fi

    _restart_app
    echo "  Migration recovery attempted. Verify with /health" | tee -a "${RECOVERY_LOG}"
}

# =============================================================================
# Recovery: Restart failure
# =============================================================================

_recover_restart() {
    echo "[RECOVERY] Restart failure detected" | tee -a "${RECOVERY_LOG}"

    # Check for common issues
    if [ -f "gunicorn.pid" ]; then
        echo "  Removing stale PID file..." | tee -a "${RECOVERY_LOG}"
        rm -f gunicorn.pid
    fi

    # Check port conflicts
    if ss -tlnp 2>/dev/null | grep -q ":8000 "; then
        echo "  Port 8000 in use — checking..." | tee -a "${RECOVERY_LOG}"
        ss -tlnp 2>/dev/null | grep ":8000 " | tee -a "${RECOVERY_LOG}"
    fi

    # Try force restart
    echo "  Attempting force restart..." | tee -a "${RECOVERY_LOG}"
    if command -v docker-compose &> /dev/null; then
        docker-compose down web 2>&1 || true
        docker-compose up -d web 2>&1 | tee -a "${RECOVERY_LOG}"
    elif command -v systemctl &> /dev/null; then
        sudo systemctl stop shunya 2>&1 || true
        sleep 2
        sudo systemctl start shunya 2>&1 | tee -a "${RECOVERY_LOG}"
    fi

    sleep 5
    HEALTH=$(_health_check)
    if [ "${HEALTH}" != "unreachable" ]; then
        echo "  Force restart successful" | tee -a "${RECOVERY_LOG}"
    else
        echo "  CRITICAL: Application still not responding after restart" | tee -a "${RECOVERY_LOG}"
        echo "  Manual steps:" | tee -a "${RECOVERY_LOG}"
        echo "    1. docker-compose logs web (check errors)" | tee -a "${RECOVERY_LOG}"
        echo "    2. Check DATABASE_URL connectivity" | tee -a "${RECOVERY_LOG}"
        echo "    3. Check SECRET_KEY is set" | tee -a "${RECOVERY_LOG}"
    fi
}

# =============================================================================
# Recovery: Complete system failure
# =============================================================================

_recover_complete() {
    echo "[RECOVERY] Complete system failure — running full recovery" | tee -a "${RECOVERY_LOG}"

    # Step 1: Check Docker / system health
    echo "  Step 1: Checking infrastructure..." | tee -a "${RECOVERY_LOG}"
    if command -v docker &> /dev/null; then
        docker info > /dev/null 2>&1 && echo "  Docker: running" || echo "  Docker: NOT running" | tee -a "${RECOVERY_LOG}"
    fi

    # Step 2: Ensure .env exists
    if [ ! -f ".env" ]; then
        echo "  Step 2: .env missing — restoring from example" | tee -a "${RECOVERY_LOG}"
        cp infrastructure/environments/production.env .env
        echo "  WARNING: .env restored from template — update secrets!" | tee -a "${RECOVERY_LOG}"
    fi

    # Step 3: Build and start
    echo "  Step 3: Starting services..." | tee -a "${RECOVERY_LOG}"
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d --build 2>&1 | tee -a "${RECOVERY_LOG}"
    fi

    # Step 4: Wait for readiness
    echo "  Step 4: Waiting for readiness..." | tee -a "${RECOVERY_LOG}"
    for i in $(seq 1 10); do
        HEALTH=$(_health_check)
        if [ "${HEALTH}" != "unreachable" ]; then
            echo "  Application responding" | tee -a "${RECOVERY_LOG}"
            break
        fi
        echo "  Attempt ${i}/10..." | tee -a "${RECOVERY_LOG}"
        sleep 3
    done

    # Step 5: Run health check
    echo "  Step 5: Health check..." | tee -a "${RECOVERY_LOG}"
    HEALTH=$(_health_check)
    echo "  Health: ${HEALTH}" | tee -a "${RECOVERY_LOG}"

    if [ "${HEALTH}" != "unreachable" ]; then
        echo "RECOVERY COMPLETE" | tee -a "${RECOVERY_LOG}"
    else
        echo "CRITICAL: Full recovery failed — manual intervention required" | tee -a "${RECOVERY_LOG}"
        return 1
    fi
}

# =============================================================================
# Main
# =============================================================================

case "${SCENARIO}" in
    deployment)
        _recover_deployment
        ;;
    migration)
        _recover_migration
        ;;
    restart)
        _recover_restart
        ;;
    complete)
        _recover_complete
        ;;
    *)
        echo "Usage: $0 {deployment|migration|restart|complete}"
        exit 1
        ;;
esac

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SHUNYA recovery completed: ${SCENARIO}" | tee -a "${RECOVERY_LOG}"
echo "Log: ${RECOVERY_LOG}"