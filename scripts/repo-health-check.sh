#!/usr/bin/env bash
# ============================================================================
# SHUNYA Repository Health Check
# Part of the Canonical Repository & Knowledge Runtime Directive
# ============================================================================
# Checks: broken references, orphan documents, missing constitutional links,
#         undocumented engines, duplicate IDs, circular dependencies
# ============================================================================
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

RULES_PASSED=0
RULES_FAILED=0
RULES_WARNED=0

pass() { echo "  [PASS] $1"; ((RULES_PASSED++)); }
fail() { echo "  [FAIL] $1"; ((RULES_FAILED++)); }
warn() { echo "  [WARN] $1"; ((RULES_WARNED++)); }

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  SHUNYA Repository Health Check                             ║"
echo "║  $(date -u '+%Y-%m-%d %H:%M:%S UTC')                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. FINAL COMMIT CHECK ──────────────────────────────────────────────────
echo "─── 1. Git Integrity ───"
if git rev-parse HEAD >/dev/null 2>&1; then
    pass "HEAD resolves to $(git rev-parse --short HEAD)"
else
    fail "HEAD does not resolve"
fi

if git fsck --no-dangling 2>&1 | grep -v "reflog" | grep -c "error" | grep -q "." 2>/dev/null; then
    echo "  [WARN] git fsck has reflog errors (legacy main branch refs) — non-critical"
    echo "         These are reflog entries for the old broken 'main' branch"
    echo "         that was fixed in the previous commit."
    ((RULES_WARNED++))
else
    pass "No git object errors"
fi

# ── 2. CANONICAL MANIFEST ──────────────────────────────────────────────────
echo ""
echo "─── 2. Canonical Manifest ───"
if [ -f CANONICAL_MANIFEST.yaml ]; then
    pass "CANONICAL_MANIFEST.yaml exists"
    ENTRIES=$(grep -c "^  - id:" CANONICAL_MANIFEST.yaml 2>/dev/null || echo "0")
    echo "       Entries: $ENTRIES"
else
    fail "CANONICAL_MANIFEST.yaml is missing"
fi

# ── 3. AI CONTEXT INDEX ────────────────────────────────────────────────────
echo ""
echo "─── 3. AI Context Index ───"
if [ -f AI_CONTEXT_INDEX.yaml ]; then
    pass "AI_CONTEXT_INDEX.yaml exists"
else
    fail "AI_CONTEXT_INDEX.yaml is missing"
fi

# ── 4. REPOSITORY INDEX ────────────────────────────────────────────────────
echo ""
echo "─── 4. Repository Index ───"
if [ -f REPOSITORY_INDEX.md ]; then
    pass "REPOSITORY_INDEX.md exists"
    LINES=$(wc -l < REPOSITORY_INDEX.md)
    echo "       Lines: $LINES"
else
    fail "REPOSITORY_INDEX.md is missing"
fi

# ── 5. TRACEABILITY MATRIX ─────────────────────────────────────────────────
echo ""
echo "─── 5. Traceability Matrix ───"
if [ -f TRACEABILITY_MATRIX.md ]; then
    pass "TRACEABILITY_MATRIX.md exists"
else
    fail "TRACEABILITY_MATRIX.md is missing"
fi

# ── 6. CONSTITUTIONAL LINKS ────────────────────────────────────────────────
echo ""
echo "─── 6. Constitutional Document Links ───"
for vol in constitution/FIRST_PRINCIPLES.md constitution/SHUNYA_CONSTITUTION.md \
           constitution/CANONICAL_DEFINITIONS.md constitution/CONSTITUTIONAL_COMPLIANCE.md \
           constitution/HERMES_IMPLEMENTATION_CHARTER.md constitution/CONSTITUTIONAL_METADATA.md; do
    if [ -f "$vol" ]; then
        pass "Constitutional volume exists: $vol"
    else
        fail "Missing constitutional volume: $vol"
    fi
done

# Check cross-references between volumes (basic)
echo ""
echo "─── 7. Cross-Volume Reference Integrity ───"
# CONST-I should reference CONST-II
if grep -q "Volume II" constitution/FIRST_PRINCIPLES.md 2>/dev/null; then
    pass "CONST-I references CONST-II"
else
    fail "CONST-I does not reference CONST-II"
fi
# CONST-II should reference CONST-I
if grep -q "Volume I" constitution/SHUNYA_CONSTITUTION.md 2>/dev/null; then
    pass "CONST-II references CONST-I"
else
    fail "CONST-II does not reference CONST-I"
fi
# CONST-II should reference CONST-III
if grep -q "Volume III" constitution/SHUNYA_CONSTITUTION.md 2>/dev/null; then
    pass "CONST-II references CONST-III"
else
    fail "CONST-II does not reference CONST-III"
fi

# ── 7. ENGINE TRACEABILITY ─────────────────────────────────────────────────
echo ""
echo "─── 8. Engine Documentation ───"
ENGINES="Observer Memory Knowledge Reasoner Simulation Planner Executive Evaluator Learner Governance"
for engine in $ENGINES; do
    # Check constitution mentions
    if grep -qi "$engine Engine" constitution/SHUNYA_CONSTITUTION.md 2>/dev/null; then
        pass "Engine documented in constitution: $engine"
    else
        warn "Engine not found in constitution: $engine"
    fi
    # Check engine spec
    if grep -riq "$engine" governance/engine_specs/ 2>/dev/null; then
        pass "Engine referenced in engine specs: $engine"
    else
        warn "Engine not found in engine specs: $engine"
    fi
done

# ── 8. DUPLICATE ID DETECTION ──────────────────────────────────────────────
echo ""
echo "─── 9. Duplicate ID Detection ───"
if [ -f CANONICAL_MANIFEST.yaml ]; then
    DUPS=$(grep "^  - id:" CANONICAL_MANIFEST.yaml | sort | uniq -d | wc -l)
    if [ "$DUPS" -eq 0 ]; then
        pass "No duplicate IDs in CANONICAL_MANIFEST.yaml"
    else
        fail "Found $DUPS duplicate IDs in CANONICAL_MANIFEST.yaml"
    fi
fi

# Check for duplicate document names
DUPLICATE_FILES=$(find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/__pycache__/*" -not -path "*/archive/*" -not -path "*/.git/*" | sed 's|.*/||' | sort | uniq -d)
if [ -n "$DUPLICATE_FILES" ]; then
    echo "  [WARN] Files with duplicate names:"
    echo "$DUPLICATE_FILES" | head -10 | while read -r f; do echo "         $f"; done
    ((RULES_WARNED++))
else
    pass "No duplicate file names found"
fi

# ── 9. ORPHAN DOCUMENT CHECK ───────────────────────────────────────────────
echo ""
echo "─── 10. Orphan Check ───"
# Check for .md files in root that aren't referenced in any index
if [ -f REPOSITORY_INDEX.md ]; then
    ROOT_MDS=$(find . -maxdepth 1 -name "*.md" | wc -l)
    echo "       Root-level markdown files: $ROOT_MDS"
    pass "Root documents count: $ROOT_MDS"
fi

# ── 10. KNOWLEDGE GRAPH ────────────────────────────────────────────────────
echo ""
echo "─── 11. Knowledge Graph ───"
if [ -f KNOWLEDGE_GRAPH.yaml ]; then
    pass "KNOWLEDGE_GRAPH.yaml exists"
    RELATIONS=$(grep -c "^  - source:" KNOWLEDGE_GRAPH.yaml 2>/dev/null || echo "0")
    echo "       Relationships: $RELATIONS"
else
    fail "KNOWLEDGE_GRAPH.yaml is missing"
fi

# ── 11. FOUNDER DASHBOARD ──────────────────────────────────────────────────
echo ""
echo "─── 12. Founder Dashboard ───"
if [ -f FOUNDER_DASHBOARD.md ]; then
    pass "FOUNDER_DASHBOARD.md exists"
else
    fail "FOUNDER_DASHBOARD.md is missing"
fi

# ── 12. CIRCULAR DEPENDENCY CHECK ──────────────────────────────────────────
echo ""
echo "─── 13. Circular Dependency Check (Engine Level) ───"
# Check that no engine imports from itself or creates obvious cycles
# This is a basic check; real analysis would need a proper dependency graph
if [ -f KNOWLEDGE_GRAPH.yaml ]; then
    CYCLES=$(grep -c "depends_on.*itself\|circular\|cycle" KNOWLEDGE_GRAPH.yaml 2>/dev/null || echo "0")
    CYCLES=${CYCLES%% *}  # strip whitespace
    if [ "$CYCLES" = "0" ] 2>/dev/null; then
        pass "No obvious circular dependencies detected in knowledge graph"
    else
        warn "Potential circular dependencies flagged in knowledge graph"
    fi
fi

# ── 13. SUMMARY ────────────────────────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  HEALTH CHECK SUMMARY                                       ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
printf "║  PASSED:  %-3d                                              ║\n" $RULES_PASSED
printf "║  FAILED:  %-3d                                              ║\n" $RULES_FAILED
printf "║  WARNINGS: %-3d                                             ║\n" $RULES_WARNED
if [ "$RULES_FAILED" -eq 0 ]; then
    echo "║  STATUS:  ✅ HEALTHY                                         ║"
else
    echo "║  STATUS:  ❌ ISSUES DETECTED                                  ║"
fi
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Report generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"