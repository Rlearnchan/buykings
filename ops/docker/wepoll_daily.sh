#!/usr/bin/env bash
set -euo pipefail

cd /app

target_date="${WEPOLL_TARGET_DATE:-$(TZ=Asia/Seoul date -d 'yesterday' +%F)}"
fetcher_url="${WEPOLL_FETCHER_URL:-http://wepoll-fetcher:8777}"
python_bin="${WEPOLL_PYTHON:-python3}"
download_dir="${WEPOLL_DOWNLOAD_DIR:-/app/runtime/downloads/wepoll}"
manifest_dir="${WEPOLL_MANIFEST_DIR:-/app/runtime/logs/wepoll-fetcher}"

echo "Wepoll daily run: target_date=${target_date} fetcher=${fetcher_url}"

for attempt in $(seq 1 "${WEPOLL_HEALTH_RETRIES:-10}"); do
  if curl -fsS "${fetcher_url%/}/health" >/tmp/wepoll-health.json; then
    cat /tmp/wepoll-health.json
    break
  fi
  if [[ "$attempt" == "${WEPOLL_HEALTH_RETRIES:-10}" ]]; then
    echo "Fetcher health check failed after ${attempt} attempts." >&2
    exit 1
  fi
  sleep "${WEPOLL_HEALTH_RETRY_SECONDS:-15}"
done

args=(
  "scripts/run_wepoll_daily_from_fetcher.py"
  "--fetcher-url" "$fetcher_url"
  "--target-date" "$target_date"
  "--download-dir" "$download_dir"
  "--manifest-dir" "$manifest_dir"
  "--python-executable" "$python_bin"
)

if [[ -n "${WEPOLL_MIN_ROWS:-}" ]]; then
  args+=("--min-rows" "$WEPOLL_MIN_ROWS")
fi

if [[ -n "${WEPOLL_FETCHER_OUTPUT_DIR:-}" ]]; then
  args+=("--fetcher-output-dir" "$WEPOLL_FETCHER_OUTPUT_DIR")
fi

if [[ "${WEPOLL_SKIP_APPEND:-0}" == "1" ]]; then
  args+=("--skip-append")
fi

if [[ "${WEPOLL_SKIP_PUBLISH:-0}" == "1" ]]; then
  args+=("--skip-publish")
fi

if [[ "${WEPOLL_SKIP_SQLITE_SYNC:-0}" == "1" ]]; then
  args+=("--skip-sqlite-sync")
fi

"$python_bin" "${args[@]}"
