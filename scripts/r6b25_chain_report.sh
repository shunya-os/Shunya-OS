#!/bin/bash
# R6B-2.5 — compact report of where the canonical chain stops.
set -u
CERTDB="${1:-shunya_r6b25_cert}"
LOG="/home/shunya-deploy/shunya_os/artifacts/r6b25/bootstrap_$CERTDB.log"
[ -f "$LOG" ] || { echo "no log yet: $LOG"; exit 1; }

echo "=== boot probe result ==="
grep -E "^(dialect|server_version|database|tables_after_create_all):" "$LOG"
grep -E "^### STEP1_EXIT=" "$LOG"

echo "=== revisions attempted ==="
grep -c "Running upgrade" "$LOG"

echo "=== last revision reached ==="
grep "Running upgrade" "$LOG" | tail -1

echo "=== failure class ==="
grep -E "psycopg2\.errors\.[A-Za-z]+|sqlalchemy\.exc\.[A-Za-z]+" "$LOG" | tail -3

echo "=== failing SQL ==="
grep -E "^\[SQL: " "$LOG" | tail -3

echo "=== failure site (migration file:line) ==="
grep -E "migrations/versions/.*\.py\", line" "$LOG" | tail -3

echo "=== STEP2_EXIT ==="
grep -E "^### STEP2_EXIT=" "$LOG"
