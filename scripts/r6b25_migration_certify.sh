#!/bin/bash
# R6B-2.5 — PostgreSQL migration certification on a FRESH disposable database.
#
# Proves the canonical initialization path reproducibly reaches Alembic head:
#
#   0. drop + create a fresh database            (disposable cluster, port 5433)
#   1. canonical boot: db.create_all()           (app/__init__.py, the real path)
#   2. alembic heads
#   3. alembic current
#   4. alembic upgrade head                      (first run)
#   5. alembic upgrade head                      (second run — must be a no-op)
#   6. schema artifact verification
#
# NO manual ALTER TABLE. NO manual CREATE INDEX. NO `alembic stamp`.
#
# Run from the repository root. No PYTHONPATH override: migrations/env.py
# already puts the repository root on sys.path, so the app resolves normally.
set -u

REPO=/home/shunya-deploy/shunya_os
CERTDB="${1:-shunya_r6b25_cert}"
PY="$REPO/.venv/bin/python"
PSQL=/usr/lib/postgresql/16/bin/psql
ART="$REPO/artifacts/r6b25"
LOG="$ART/migration_certification_$CERTDB.log"

mkdir -p "$ART"
: > "$LOG"

cd "$REPO" || exit 1
export PGHOST=127.0.0.1 PGPORT=5433 PGUSER=shunya-deploy
export DATABASE_URL="postgresql://shunya-deploy@127.0.0.1:5433/$CERTDB"

log() { echo "$@" | tee -a "$LOG"; }
q() { $PSQL -d "$CERTDB" -tAc "$1" 2>&1; }

FAILED=0

log "### R6B-2.5 PostgreSQL migration certification (fresh disposable database)"
log "### date=$(date -Is)"
log "### repository_sha=$(git rev-parse HEAD)"
log "### database=$CERTDB"
log "### DATABASE_URL=$DATABASE_URL"
log "### pg_server_version=$(q 'SHOW server_version')"
log "### cluster_datadir=/home/shunya-deploy/shunya-cert-pg-r6b24/data"

log ""
log "=== 0. fresh database ==="
$PSQL -d postgres -c "DROP DATABASE IF EXISTS $CERTDB;" >>"$LOG" 2>&1
$PSQL -d postgres -c "CREATE DATABASE $CERTDB;" >>"$LOG" 2>&1
log "pre_boot_tables=$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"
log "pre_boot_alembic_version=$(q "SELECT to_regclass('public.alembic_version') IS NOT NULL")"

log ""
log "=== 1. canonical boot path (db.create_all) ==="
"$PY" scripts/r6b25_bootstrap_probe.py 2>&1 | tee -a "$LOG"
boot_exit=${PIPESTATUS[0]}
log "boot_exit=$boot_exit"
[ "$boot_exit" -ne 0 ] && FAILED=1
log "post_boot_tables=$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"
log "post_boot_alembic_version=$(q "SELECT to_regclass('public.alembic_version') IS NOT NULL")"

log ""
log "=== 2. alembic heads ==="
"$PY" -m alembic heads 2>&1 | tee -a "$LOG"
HEADS_EXIT=${PIPESTATUS[0]}
log "heads_exit=$HEADS_EXIT"

log ""
log "=== 3. alembic current (before chain) ==="
"$PY" -m alembic current 2>&1 | tee -a "$LOG"

log ""
log "=== 4. alembic upgrade head (first run) ==="
"$PY" -m alembic upgrade head 2>&1 | tee -a "$LOG"
first_exit=${PIPESTATUS[0]}
log "first_upgrade_exit=$first_exit"
[ "$first_exit" -ne 0 ] && FAILED=1
FIRST_RUN_LINES=$(grep -c "Running upgrade" "$LOG" || true)
log "revisions_executed_first_run=$FIRST_RUN_LINES"

log ""
log "=== 5. alembic current (after first run) ==="
"$PY" -m alembic current 2>&1 | tee -a "$LOG"

log ""
log "=== 6. alembic upgrade head (second run — must execute no revision) ==="
SECOND_LOG="$ART/.second_run.tmp"
"$PY" -m alembic upgrade head >"$SECOND_LOG" 2>&1
second_exit=$?
cat "$SECOND_LOG" >>"$LOG"
second_run_lines=$(grep -c "Running upgrade" "$SECOND_LOG" || true)
log "second_upgrade_exit=$second_exit"
log "revisions_executed_second_run=$second_run_lines"
[ "$second_exit" -ne 0 ] && FAILED=1
[ "$second_run_lines" -ne 0 ] && FAILED=1

log ""
log "=== 7. schema artifact verification ==="
log "alembic_version_rows=$(q 'SELECT count(*) FROM alembic_version')"
log "alembic_version_head=$(q 'SELECT version_num FROM alembic_version')"
log "commitments_table=$(q "SELECT to_regclass('public.commitments') IS NOT NULL")"
log "commitments_tenant_id=$(q "SELECT count(*) FROM information_schema.columns WHERE table_name='commitments' AND column_name='tenant_id'")"
log "ix_commitments_tenant=$(q "SELECT count(*) FROM pg_indexes WHERE indexname='ix_commitments_tenant'")"
log "evidence_records_tenant_id=$(q "SELECT count(*) FROM information_schema.columns WHERE table_name='evidence_records' AND column_name='tenant_id'")"
log "objects_tenant_id=$(q "SELECT count(*) FROM information_schema.columns WHERE table_name='objects' AND column_name='tenant_id'")"
log "act_execution_logs_tenant_id=$(q "SELECT count(*) FROM information_schema.columns WHERE table_name='act_execution_logs' AND column_name='tenant_id'")"
log "ix_exec_tenant=$(q "SELECT count(*) FROM pg_indexes WHERE indexname='ix_exec_tenant'")"
log "sh_workspaces_org_fk=$(q "SELECT count(*) FROM pg_constraint WHERE conname='sh_workspaces_organization_id_fkey'")"
log "sh_objects_org_fk=$(q "SELECT count(*) FROM pg_constraint WHERE conname='sh_objects_organization_id_fkey'")"
log "public_table_count=$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"

log ""
log "=== 8. outcome ==="
if [ "$FAILED" -eq 0 ]; then
  log "MIGRATION_CERTIFICATION=PASS"
else
  log "MIGRATION_CERTIFICATION=FAIL"
fi
echo "LOG=$LOG"
exit $FAILED
