#!/bin/bash
# R6B-2.5 — reproduce the canonical initialization path on a FRESH disposable DB
# Path under test = the supported deployment path:
#   1) application boot  -> db.create_all() + default workspace seed
#   2) alembic upgrade head
# No manual ALTER TABLE. No manual CREATE INDEX. No manual alembic stamp.
set -u

CERTDB="${1:-shunya_r6b25_cert}"
export PGHOST=127.0.0.1 PGPORT=5433 PGUSER=shunya-deploy
PSQL=/usr/lib/postgresql/16/bin/psql
REPO=/home/shunya-deploy/shunya_os
PY="$REPO/.venv/bin/python"

cd "$REPO" || exit 1
export PYTHONPATH="$REPO"
export DATABASE_URL="postgresql://shunya-deploy@127.0.0.1:5433/$CERTDB"

ART="$REPO/artifacts/r6b25"
mkdir -p "$ART"
LOG="$ART/bootstrap_$CERTDB.log"
: > "$LOG"

log() { echo "$@" | tee -a "$LOG"; }

log "### R6B-2.5 canonical bootstrap: db=$CERTDB"
log "### date=$(date -Is) host=$(hostname)"

echo "### STEP 0 — drop + create fresh database: $CERTDB"
$PSQL -d postgres -c "DROP DATABASE IF EXISTS $CERTDB;" >>"$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ]; then echo "FATAL: drop failed"; exit 1; fi
$PSQL -d postgres -c "CREATE DATABASE $CERTDB;" >>"$LOG" 2>&1
rc=$?
if [ $rc -ne 0 ]; then echo "FATAL: create failed"; exit 1; fi
log "### DATABASE_URL=$DATABASE_URL"

echo "### STEP 1 — canonical app boot path (db.create_all())"
"$PY" scripts/r6b25_bootstrap_probe.py >>"$LOG" 2>&1
log "### STEP1_EXIT=$?"

echo "### STEP 2 — alembic upgrade head"
"$PY" -m alembic upgrade head >>"$LOG" 2>&1
log "### STEP2_EXIT=$?"

echo "$LOG"