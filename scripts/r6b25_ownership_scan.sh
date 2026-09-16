#!/bin/bash
# R6B-2.5 Window 3 — zero-trust ownership rescan.
# Reports every occurrence of synthetic/arbitrary ownership patterns.
# Read-only.
cd /home/shunya-deploy/shunya_os || exit 1

PATTERNS=(
  'organization_id[[:space:]]*=[[:space:]]*0'
  'org_id[[:space:]]*=[[:space:]]*0'
  'tenant_id[[:space:]]*=[[:space:]]*0'
  'organization_id=0|org_id=0|tenant_id=0'
  'organization_id[[:space:]]*=[[:space:]]*1\b'
  'org_id[[:space:]]*=[[:space:]]*1\b'
  'tenant_id[[:space:]]*=[[:space:]]*1\b'
  'Organization\.query\.first\(\)'
  'Workspace\.query\.filter_by\(status'
  'filter_by\(status="active"\)\.first\(\)'
  'spc_personal'
  'spc_business'
  'spc_custom'
  'FounderSpace\.query'
  'FounderObject\b'
  'founder_objects'
  'or 0\b'
)

for p in "${PATTERNS[@]}"; do
  echo "==================== PATTERN: $p"
  grep -rn --include=*.py -E "$p" app/ core/ migrations/ scripts/ 2>/dev/null \
    | grep -v "__pycache__" \
    | head -40
done
