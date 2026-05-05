#!/usr/bin/env bash
set -u

cd /app

run_date="${AUTOPARK_RETRO_DATE:-${AUTOPARK_DATE:-$(TZ=Asia/Seoul date +%F)}}"
attempts="${AUTOPARK_RETRO_ATTEMPTS:-1}"
sleep_minutes="${AUTOPARK_RETRO_SLEEP_MINUTES:-0}"
timeout_label="${AUTOPARK_RETRO_LABEL:-manual post-broadcast retrospective}"

args=(
  "projects/autopark/scripts/run_broadcast_retrospective.py"
  "--date" "$run_date"
  "--attempts" "$attempts"
  "--sleep-minutes" "$sleep_minutes"
  "--python" "python3"
)

if [[ -n "${AUTOPARK_RETRO_VIDEO_URL:-}" ]]; then
  args+=("--video-url" "$AUTOPARK_RETRO_VIDEO_URL")
fi

if [[ -n "${AUTOPARK_RETRO_VIDEO_ID:-}" ]]; then
  args+=("--video-id" "$AUTOPARK_RETRO_VIDEO_ID")
fi

if [[ -n "${AUTOPARK_RETRO_PPT:-}" ]]; then
  args+=("--ppt" "$AUTOPARK_RETRO_PPT")
fi

if [[ -n "${AUTOPARK_RETRO_LOCAL_TRANSCRIPT:-}" ]]; then
  args+=("--local-transcript" "$AUTOPARK_RETRO_LOCAL_TRANSCRIPT")
fi

if [[ "${AUTOPARK_RETRO_SKIP_PPT_OUTLINE:-0}" == "1" ]]; then
  args+=("--skip-ppt-outline")
fi

if [[ "${AUTOPARK_RETRO_SKIP_ACTUAL_OUTLINE:-0}" == "1" ]]; then
  args+=("--skip-actual-outline")
fi

if [[ "${AUTOPARK_RETRO_SKIP_ASSET_COMPARISON:-0}" == "1" ]]; then
  args+=("--skip-asset-comparison")
fi

if [[ "${AUTOPARK_RETRO_SKIP_RETROSPECTIVE:-0}" == "1" ]]; then
  args+=("--skip-retrospective")
fi

if [[ "${AUTOPARK_RETRO_DRY_RUN:-0}" == "1" ]]; then
  args+=("--dry-run")
fi

echo "Autopark ${timeout_label}: date=${run_date} attempts=${attempts} sleep_minutes=${sleep_minutes}"
python3 "${args[@]}"
