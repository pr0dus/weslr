#!/bin/bash
# WESLR Protected Chat Shell — Deploy Script
# Owner-only: requires sudo for the rsync to /var/www/weslr-chat-app-shell/
# 
# This script does FOUR things:
#  1. Backs up the current deployed file
#  2. rsyncs the patched source into place
#  3. Fixes ownership and permissions
#  4. Verifies source/deployed match
#
# Run from a sudo-capable terminal:
#   bash docs/NOVA_PROTECTED_CHAT_DEPLOY_AND_BACKEND_PREVIEW_START_V1.md.deploy.sh
#
# The patched source is at:
#   /home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell/index.html
# (commit 55fb839, contains /api/auth/me + Owner Preview logic)

set -euo pipefail

SRC="/home/pr0/projects/weslr-v1-ui-website/protected-preview/chat-app-shell"
DST="/var/www/weslr-chat-app-shell"
BACKUP_DIR="/var/backups/weslr-chat-app-shell"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_PATH="${BACKUP_DIR}/index.html.before-auth-status-${TS}.bak"

echo "[1/4] Creating backup directory and snapshotting current deployed file..."
sudo mkdir -p "$BACKUP_DIR"
sudo cp -a "$DST/index.html" "$BACKUP_PATH"
echo "  Backup: $BACKUP_PATH"
echo

echo "[2/4] rsync patched source to deployed path..."
sudo rsync -a --delete "$SRC/" "$DST/"
echo "  rsync complete"
echo

echo "[3/4] Fixing ownership and permissions..."
sudo chown -R root:www-data "$DST"
sudo find "$DST" -type d -exec chmod 755 {} \;
sudo find "$DST" -type f -exec chmod 644 {} \;
echo "  ownership=root:www-data perms=755/644 applied"
echo

echo "[4/4] Verifying source/deployed match..."
if cmp -s "$SRC/index.html" "$DST/index.html"; then
  echo "  SOURCE_DEPLOYED_MATCH"
else
  echo "  SOURCE_DEPLOYED_DIFFER — check permissions or rsync logs"
  exit 1
fi

echo
echo "=== Deploy complete ==="
echo
echo "Verification grep:"
echo "--- /api/message ---"
grep -n "fetch.*/api/message" "$DST/index.html" || echo "MISSING"
echo "--- /api/auth/me ---"
grep -n "fetch.*/api/auth/me" "$DST/index.html" || echo "MISSING"
echo "--- Owner Preview ---"
grep -n "Owner Preview" "$DST/index.html" || echo "MISSING"
echo "--- stale text (should be 0) ---"
echo "  Backend not connected: $(grep -c "Backend not connected" "$DST/index.html" || echo 0)"
echo "  UI Preview Only:       $(grep -c "UI Preview Only" "$DST/index.html" || echo 0)"
echo
echo "Backup is at: $BACKUP_PATH"
echo "Rollback command:"
echo "  sudo cp -a $BACKUP_PATH $DST/index.html && sudo chown root:www-data $DST/index.html && sudo chmod 644 $DST/index.html"
