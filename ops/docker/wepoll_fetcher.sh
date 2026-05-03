#!/usr/bin/env bash
set -euo pipefail

cd /app

args=(
  "scripts/wepoll_fetcher_daemon.mjs"
  "--user-data-dir" "${WEPOLL_FETCHER_USER_DATA_DIR:-/state/fetcher-profile}"
  "--host" "${WEPOLL_FETCHER_HOST:-0.0.0.0}"
  "--port" "${WEPOLL_FETCHER_PORT:-8777}"
  "--verbose"
)

if [[ "${WEPOLL_FETCHER_HEADED:-0}" == "1" ]]; then
  args+=("--headed")
fi

if [[ "${WEPOLL_ALLOW_MANUAL_LOGIN:-0}" == "1" ]]; then
  args+=("--allow-manual-login")
fi

echo "Wepoll fetcher starting: host=${WEPOLL_FETCHER_HOST:-0.0.0.0} port=${WEPOLL_FETCHER_PORT:-8777} headed=${WEPOLL_FETCHER_HEADED:-0}"
if [[ "${WEPOLL_FETCHER_HEADED:-0}" == "1" ]] && command -v xvfb-run >/dev/null 2>&1; then
  xvfb-run -a node "${args[@]}"
else
  node "${args[@]}"
fi
