#!/usr/bin/env bash
set -u

cd /app

run_date="${AUTOPARK_DATE:-$(TZ=Asia/Seoul date +%F)}"
timeout_seconds="${AUTOPARK_STEP_TIMEOUT:-120}"

if [[ "${AUTOPARK_CDP_ENDPOINT:-}" == *host.docker.internal* ]]; then
  resolved_host="$(
    getent ahostsv4 host.docker.internal \
      | awk 'index($1, ".") > 0 {print $1; exit}'
  )"
  if [[ -n "$resolved_host" ]]; then
    endpoint_path="${AUTOPARK_CDP_ENDPOINT#*host.docker.internal}"
    export AUTOPARK_CDP_ENDPOINT="http://${resolved_host}${endpoint_path}"
  fi
fi

if [[ -n "${AUTOPARK_START_AT:-}" ]]; then
  target_epoch="$(TZ=Asia/Seoul date -d "${run_date} ${AUTOPARK_START_AT}" +%s)"
  now_epoch="$(TZ=Asia/Seoul date +%s)"
  if (( target_epoch <= now_epoch )); then
    target_epoch=$(( target_epoch + 24 * 3600 ))
  fi
  sleep_seconds=$(( target_epoch - now_epoch ))
  target_label="$(TZ=Asia/Seoul date -d "@${target_epoch}" "+%Y-%m-%d %H:%M:%S %Z")"
  echo "Autopark container waiting until ${target_label} (${sleep_seconds}s)"
  sleep "$sleep_seconds"
fi

args=(
  "projects/autopark/scripts/run_live_dashboard_all_in_one.py"
  "--date" "$run_date"
  "--timeout" "$timeout_seconds"
)

if [[ "${AUTOPARK_SKIP_CHROME_LAUNCH:-1}" == "1" ]]; then
  args+=("--skip-chrome-launch")
fi

if [[ "${AUTOPARK_SKIP_DATAWRAPPER_EXPORT:-1}" == "1" ]]; then
  args+=("--skip-datawrapper-export")
fi

if [[ "${AUTOPARK_SKIP_PUBLISH:-1}" == "1" ]]; then
  args+=("--skip-publish" "--publish-policy" "never")
else
  args+=("--publish-policy" "${AUTOPARK_PUBLISH_POLICY:-gate}")
fi

echo "Autopark container run: date=${run_date} use_cdp=${AUTOPARK_USE_CDP:-1} cdp=${AUTOPARK_CDP_ENDPOINT:-unset} publish_skipped=${AUTOPARK_SKIP_PUBLISH:-1}"
python3 "${args[@]}"
