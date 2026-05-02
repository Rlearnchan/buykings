#!/usr/bin/env bash
set -euo pipefail

profile_dir="${AUTOPARK_BROWSER_PROFILE_DIR:-/state/browser-profile}"
port="${AUTOPARK_BROWSER_PORT:-9222}"
host="${AUTOPARK_BROWSER_HOST:-0.0.0.0}"
chrome_path="${AUTOPARK_CHROME_PATH:-/ms-playwright/chromium-1217/chrome-linux64/chrome}"
headless="${AUTOPARK_BROWSER_HEADLESS:-1}"

mkdir -p "$profile_dir"
rm -f \
  "$profile_dir/SingletonLock" \
  "$profile_dir/SingletonSocket" \
  "$profile_dir/SingletonCookie"

args=(
  "--remote-debugging-address=${host}"
  "--remote-debugging-port=${port}"
  "--user-data-dir=${profile_dir}"
  "--profile-directory=Default"
  "--no-first-run"
  "--no-default-browser-check"
  "--disable-dev-shm-usage"
  "--disable-session-crashed-bubble"
  "--disable-search-engine-choice-screen"
  "--disable-blink-features=AutomationControlled"
  "--window-size=${AUTOPARK_BROWSER_WINDOW_SIZE:-1440,1200}"
)

if [[ "${AUTOPARK_BROWSER_NO_SANDBOX:-1}" == "1" ]]; then
  args+=("--no-sandbox")
fi

args+=("${AUTOPARK_BROWSER_START_URL:-https://finviz.com/map.ashx?t=sec}")

echo "Autopark browser starting: host=${host} port=${port} profile=${profile_dir} headless=${headless}"

if [[ "$headless" == "1" ]]; then
  exec "$chrome_path" "--headless=new" "${args[@]}"
fi

if command -v xvfb-run >/dev/null 2>&1; then
  exec xvfb-run -a "$chrome_path" "${args[@]}"
fi

echo "xvfb-run unavailable; falling back to headless Chromium" >&2
exec "$chrome_path" "--headless=new" "${args[@]}"
