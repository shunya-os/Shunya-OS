#!/usr/bin/env bash
# =============================================================================
# SHUNYA — Deploy pre-flight guard (R6B-2.7 Window 6, §3)
# =============================================================================
# A deployment must NEVER destroy a developer's uncommitted work.
#
# History: deploy.sh Step 3 ran `git reset --hard <sha>` BEFORE any cleanliness
# check, silently discarding local commits and edits. This guard runs BEFORE any
# checkout/reset and FAILS CLOSED when the tree is dirty or holds unexpected
# untracked files.
#
# Exit codes:
#   0 — tree is clean and expected; safe to deploy
#   1 — tree is dirty / unexpected; refuse to deploy (nothing was modified)
#
# Usage:  bash deploy_preflight.sh [repo_dir]
# =============================================================================
set -uo pipefail

REPO_DIR="${1:-$(pwd)}"

if [[ ! -d "${REPO_DIR}/.git" ]]; then
    echo "ERROR: ${REPO_DIR} is not a git working tree" >&2
    exit 1
fi

cd "${REPO_DIR}" || exit 1

DIRTY_TRACKED=$(git status --porcelain --untracked-files=no)
if [[ -n "${DIRTY_TRACKED}" ]]; then
    echo "ERROR: Working tree has uncommitted changes — refusing to deploy so no work is destroyed." >&2
    echo "${DIRTY_TRACKED}" >&2
    echo "       Commit, stash or discard them deliberately, then re-run." >&2
    exit 1
fi

UNTRACKED_FILES=$(git ls-files --others --exclude-standard)
if [[ -n "${UNTRACKED_FILES}" ]]; then
    echo "ERROR: Deploy tree contains untracked files — refusing to deploy (unexpected state)." >&2
    echo "${UNTRACKED_FILES}" | head -20 >&2
    exit 1
fi

echo "Deploy pre-flight: tree clean — safe to proceed."
exit 0
