#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_CHROME_DIR="${SOURCE_CHROME_DIR:-$HOME/Library/Application Support/Google/Chrome}"
SOURCE_PROFILE="${SOURCE_PROFILE:-Profile 1}"
TARGET_PROFILE="${TARGET_PROFILE:-finviz}"
TARGET_DIR="${TARGET_DIR:-$ROOT_DIR/runtime/profiles/$TARGET_PROFILE}"

mkdir -p "$TARGET_DIR/Default"

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
  "$TARGET_DIR/Default/"

cp "$SOURCE_CHROME_DIR/Local State" "$TARGET_DIR/Local State"

echo "Chrome profile synced for Playwright:"
echo "  source: $SOURCE_CHROME_DIR/$SOURCE_PROFILE"
echo "  target: $TARGET_DIR/Default"
