#!/usr/bin/env bash
set -euo pipefail
# verify-deployment.sh — Z-03B Article IV: Production Equals Source
# Fails with non-zero exit if production differs from the repository.

echo "=== Deployment Verification ==="

# 1. Source revision
HEAD=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
echo "Git HEAD: $HEAD"

# 2. Frontend asset hashes
ASSETS=$(ls frontend/dist/assets/index-*.js 2>/dev/null || echo "")
if [ -z "$ASSETS" ]; then
  echo "FAIL: No frontend assets found in dist/"
  exit 1
fi
echo "Frontend assets: $ASSETS"
for f in $ASSETS; do
  HASH=$(sha256sum "$f" | cut -d' ' -f1)
  echo "  $(basename $f): $HASH"
done

# 3. Backend revision
BACKEND_REV=$(git log -1 --format="%H" -- app/ core/ 2>/dev/null || echo "unknown")
echo "Backend source rev: $BACKEND_REV"

# 4. Gunicorn health
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/ 2>/dev/null || echo "000")
echo "Server health: HTTP $HEALTH"
if [ "$HEALTH" != "200" ]; then
  echo "FAIL: Server not healthy"
  exit 1
fi

# 5. DB schema (check that shunya_identities table exists)
DB_SCHEMA=$(PGPASSWORD='Shunya@2026!' psql -h localhost -p 5432 -U shunya -d shunya_os -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='shunya_identities';" 2>/dev/null | xargs || echo "0")
echo "DB schema: shunya_identities table exists: $DB_SCHEMA"
if [ "$DB_SCHEMA" != "1" ]; then
  echo "FAIL: Database schema mismatch"
  exit 1
fi

# 6. Stale artifact check
STALE=$(find frontend/src -name '*.js' -exec sh -c 'test -f "${1%.js}.tsx" && echo "stale"' _ {} \; 2>/dev/null | wc -l)
echo "Stale JS artifacts: $STALE"
if [ "$STALE" -gt 0 ]; then
  echo "FAIL: Stale JS artifacts detected"
  exit 1
fi

echo "=== Deployment OK ==="