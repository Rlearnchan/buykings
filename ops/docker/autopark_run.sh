#!/usr/bin/env bash
set -u

cd /app

run_date="${AUTOPARK_DATE:-$(TZ=Asia/Seoul date +%F)}"
timeout_seconds="${AUTOPARK_STEP_TIMEOUT:-120}"

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

echo "Autopark container run: date=${run_date} cdp=${AUTOPARK_CDP_ENDPOINT:-unset} publish_skipped=${AUTOPARK_SKIP_PUBLISH:-1}"
python3 "${args[@]}"
