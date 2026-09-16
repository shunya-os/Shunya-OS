#!/bin/bash
# R6B-2.5 Window 3 — zero-trust ownership rescan, production code only.
# Excludes comment-only lines so the output is the real remaining surface.
cd /home/shunya-deploy/shunya_os || exit 1

PATTERNS=(
  'organization_id[[:space:]]*=[[:space:]]*0'
  'org_id[[:space:]]*=[[:space:]]*0'
  'tenant_id[[:space:]]*=[[:space:]]*0'
  'organization_id[[:space:]]*=[[:space:]]*1\b'
  'org_id[[:space:]]*=[[:space:]]*1\b'
  'tenant_id[[:space:]]*=[[:space:]]*1\b'
  '\bor 0\b'
  'Organization\.query\.first\(\)'
  'Workspace\.query\.filter_by\(status'
  'filter_by\(status="active"\)\.first\(\)'
  'spc_personal|spc_business|spc_custom'
  'FounderSpace\.query'
  'FounderObject\b|founder_objects'
)

for p in "${PATTERNS[@]}"; do
  hits=$(grep -rn --include=*.py -E "$p" app/ core/ 2>/dev/null \
        | grep -v "__pycache__" \
        | grep -vE ':[0-9]+:[[:space:]]*#' )
  if [ -n "$hits" ]; then
    echo "==================== $p"
    echo "$hits"
  fi
done
echo "==================== END"
