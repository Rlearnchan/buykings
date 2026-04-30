#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_CHROME_DIR="${SOURCE_CHROME_DIR:-$HOME/Library/Application Support/Google/Chrome}"
SOURCE_PROFILE="${SOURCE_PROFILE:-Profile 1}"
TARGET_DIR="${TARGET_DIR:-$ROOT_DIR/runtime/profiles/chrome-cdp-profile}"
PORT="${PORT:-9222}"
START_URL="${START_URL:-https://x.com/wallstengine}"

mkdir -p "$TARGET_DIR/$SOURCE_PROFILE"

rsync -a --delete \
  --exclude='Cache' \
  --exclude='Code Cache' \
  --exclude='GPUCache' \
  --exclude='GrShaderCache' \
  --exclude='GraphiteDawnCache' \
  --exclude='ShaderCache' \
  --exclude='Service Worker/CacheStorage' \
  --exclude='*-journal' \
  --exclude='*-shm' \
  --exclude='*-wal' \
  --exclude='LOCK' \
  --exclude='Singleton*' \
  "$SOURCE_CHROME_DIR/$SOURCE_PROFILE/" \
  "$TARGET_DIR/$SOURCE_PROFILE/"

cp "$SOURCE_CHROME_DIR/Local State" "$TARGET_DIR/Local State"

open -na "Google Chrome" --args \
  "--remote-debugging-port=$PORT" \
  "--user-data-dir=$TARGET_DIR" \
  "--profile-directory=$SOURCE_PROFILE" \
  "$START_URL"

echo "Chrome CDP profile launched:"
echo "  endpoint: http://127.0.0.1:$PORT"
echo "  profile:  $TARGET_DIR/$SOURCE_PROFILE"
