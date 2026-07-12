#!/bin/bash
# Rollback Shunya OS to the previous release tag.
# Usage: ./rollback.sh [steps=1]

set -e

STEPS=${1:-1}
cd /root/shunya_os

echo "🔄 Rolling back $STEPS commit(s)..."

# Get current tag before rolling back
OLD_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "no-tag")

# Rollback
for i in $(seq 1 $STEPS); do
    LAST=$(git tag --sort=-creatordate | head -1)
    echo "  Reverting tag: $LAST"
    git revert HEAD --no-edit || git reset --hard HEAD~1
done

NEW_SHA=$(git rev-parse HEAD)

echo "✅ Rolled back to $NEW_SHA"
echo "  From: $OLD_TAG"
echo "  To:   $NEW_SHA"

# Restart service
systemctl restart shunya.service
sleep 2

if systemctl is-active --quiet shunya.service; then
    echo "✅ Service restarted successfully"
else
    echo "❌ Service failed to start"
    systemctl status shunya.service --no-pager
    exit 1
fi

git tag "rollback-to-$(date +%Y%m%d-%H%M%S)"
echo "✅ Rollback complete"