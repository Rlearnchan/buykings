#!/usr/bin/env bash
set -u

interval_minutes="${AUTOPARK_INTERVAL_MINUTES:-30}"
duration_hours="${AUTOPARK_LOOP_DURATION_HOURS:-12}"

if (( interval_minutes < 5 )); then
  echo "AUTOPARK_INTERVAL_MINUTES must be at least 5." >&2
  exit 2
fi
if (( duration_hours < 1 )); then
  echo "AUTOPARK_LOOP_DURATION_HOURS must be at least 1." >&2
  exit 2
fi

end_epoch=$(( $(date +%s) + duration_hours * 3600 ))

echo "Autopark container loop started: every ${interval_minutes}m for ${duration_hours}h"
echo "Publish skipped: ${AUTOPARK_SKIP_PUBLISH:-1}"

while (( $(date +%s) < end_epoch )); do
  started_epoch=$(date +%s)
  bash ops/docker/autopark_run.sh
  status=$?
  if (( status != 0 )); then
    echo "Autopark run exited with status ${status}" >&2
  fi

  next_epoch=$(( started_epoch + interval_minutes * 60 ))
  sleep_seconds=$(( next_epoch - $(date +%s) ))
  if (( sleep_seconds > 0 && $(date +%s) < end_epoch )); then
    next_at=$(TZ=Asia/Seoul date -d "@${next_epoch}" "+%Y-%m-%d %H:%M:%S %Z")
    echo "Next Autopark run at ${next_at}"
    sleep "$sleep_seconds"
  fi
done

echo "Autopark container loop finished."
