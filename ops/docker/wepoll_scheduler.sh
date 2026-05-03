#!/usr/bin/env bash
set -u

cd /app

run_times="${WEPOLL_RUN_TIMES:-07:20}"
retry_times="${WEPOLL_RETRY_TIMES:-07:50}"
retry_always="${WEPOLL_RETRY_ALWAYS:-0}"

event_schedule() {
  local kind="$1"
  local times_csv="$2"
  local now_epoch="$3"
  local time_value target_epoch

  IFS=',' read -ra times <<< "$times_csv"
  for time_value in "${times[@]}"; do
    time_value="${time_value//[[:space:]]/}"
    [[ -z "$time_value" ]] && continue
    if [[ ! "$time_value" =~ ^[0-2][0-9]:[0-5][0-9]$ ]]; then
      echo "Ignoring invalid ${kind} time: ${time_value}" >&2
      continue
    fi
    target_epoch="$(TZ=Asia/Seoul date -d "$(TZ=Asia/Seoul date +%F) ${time_value}" +%s)"
    if (( target_epoch <= now_epoch )); then
      target_epoch=$(( target_epoch + 24 * 3600 ))
    fi
    printf "%s %s %s\n" "$target_epoch" "$kind" "$time_value"
  done
}

next_event() {
  local now_epoch="$1"
  {
    event_schedule "run" "$run_times" "$now_epoch"
    event_schedule "retry" "$retry_times" "$now_epoch"
  } | sort -n | head -n 1
}

last_run_status=0

echo "Wepoll daily scheduler started."
echo "Run times: ${run_times}; retry times: ${retry_times}; fetcher: ${WEPOLL_FETCHER_URL:-http://wepoll-fetcher:8777}"

while true; do
  now_epoch="$(TZ=Asia/Seoul date +%s)"
  event="$(next_event "$now_epoch")"
  if [[ -z "$event" ]]; then
    echo "No valid WEPOLL_RUN_TIMES or WEPOLL_RETRY_TIMES configured." >&2
    sleep 300
    continue
  fi

  target_epoch="$(awk '{print $1}' <<< "$event")"
  event_kind="$(awk '{print $2}' <<< "$event")"
  event_time="$(awk '{print $3}' <<< "$event")"
  sleep_seconds=$(( target_epoch - now_epoch ))
  target_label="$(TZ=Asia/Seoul date -d "@${target_epoch}" "+%Y-%m-%d %H:%M:%S %Z")"

  echo "Next Wepoll ${event_kind} at ${target_label} (${sleep_seconds}s)"
  if (( sleep_seconds > 0 )); then
    sleep "$sleep_seconds"
  fi

  if [[ "$event_kind" == "retry" && "$retry_always" != "1" && "$last_run_status" == "0" ]]; then
    echo "Skipping retry ${event_time}; previous run exited successfully."
    sleep 60
    continue
  fi

  echo "Starting Wepoll ${event_kind}: scheduled=${event_time}"
  bash ops/docker/wepoll_daily.sh
  last_run_status=$?
  if (( last_run_status != 0 )); then
    echo "Wepoll ${event_kind} exited with status ${last_run_status}" >&2
  else
    echo "Wepoll ${event_kind} completed successfully."
  fi
  sleep 60
done
