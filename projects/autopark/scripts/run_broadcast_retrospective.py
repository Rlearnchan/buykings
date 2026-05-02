#!/usr/bin/env python3
"""Run the post-broadcast Wepoll transcript fetch and Autopark retrospective."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from autopark_calendar import DEFAULT_CALENDAR, resolve_operation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return env


def now_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")


def run(cmd: list[str], timeout: int, allow_fail: bool = False) -> tuple[dict, str]:
    completed = subprocess.run(
        cmd,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=subprocess_env(),
        capture_output=True,
        timeout=timeout,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    payload: dict = {}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
            if line.startswith("{") and line.endswith("}"):
                try:
                    payload = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
    if completed.returncode != 0 and not allow_fail:
        raise RuntimeError(stderr or stdout or f"command failed: {' '.join(cmd)}")
    return payload, (stdout + "\n" + stderr).strip()


def write_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--sleep-minutes", type=float, default=60.0)
    parser.add_argument("--video-url")
    parser.add_argument("--video-id")
    parser.add_argument("--operation-mode", choices=["auto", "daily_broadcast", "monday_catchup", "no_broadcast"], default="auto")
    parser.add_argument("--broadcast-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--skip-retrospective", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    py = args.python
    started_at = now_kst()
    operation = resolve_operation(args.date, calendar_path=args.broadcast_calendar, requested_mode=args.operation_mode)
    if not operation.get("retrospective_enabled", True):
        payload = {
            "ok": True,
            "date": args.date,
            "started_at": started_at,
            "ended_at": now_kst(),
            "operation": operation,
            "fetch": {"status": "skipped_expected_no_broadcast"},
            "retrospective": {"status": "skipped_expected_no_broadcast"},
            "steps": [
                {
                    "name": "broadcast calendar",
                    "payload": {"status": "skipped_expected_no_broadcast", "operation": operation},
                    "output_tail": str(operation.get("note") or ""),
                }
            ],
        }
        log_path = PROJECT_ROOT / "runtime" / "logs" / f"{args.date}-broadcast-retrospective.json"
        if not args.dry_run:
            write_log(log_path, payload)
        payload["log"] = str(log_path)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    fetch_payload: dict = {}
    review_payload: dict = {}
    steps = []
    for attempt in range(1, max(1, args.attempts) + 1):
        cmd = [py, "projects/autopark/scripts/fetch_wepoll_transcript.py", "--date", args.date]
        if args.video_url:
            cmd.extend(["--video-url", args.video_url])
        if args.video_id:
            cmd.extend(["--video-id", args.video_id])
        if args.dry_run:
            cmd.append("--dry-run")
        fetch_payload, output = run(cmd, 240, allow_fail=True)
        steps.append({"name": "fetch wepoll transcript", "attempt": attempt, "payload": fetch_payload, "output_tail": output[-1200:]})
        if args.dry_run or fetch_payload.get("status") == "downloaded":
            break
        if attempt < args.attempts:
            time.sleep(max(0.0, args.sleep_minutes) * 60)

    if not args.skip_retrospective and (args.dry_run or fetch_payload.get("status") == "downloaded"):
        cmd = [py, "projects/autopark/scripts/build_broadcast_retrospective.py", "--date", args.date]
        if args.dry_run:
            cmd.append("--dry-run")
        review_payload, output = run(cmd, 180, allow_fail=True)
        steps.append({"name": "build broadcast retrospective", "payload": review_payload, "output_tail": output[-1200:]})
    else:
        steps.append({"name": "build broadcast retrospective", "payload": {"status": "skipped"}, "output_tail": ""})

    payload = {
        "ok": not any(step.get("payload", {}).get("ok") is False for step in steps),
        "date": args.date,
        "started_at": started_at,
        "ended_at": now_kst(),
        "operation": operation,
        "fetch": fetch_payload,
        "retrospective": review_payload,
        "steps": steps,
    }
    log_path = PROJECT_ROOT / "runtime" / "logs" / f"{args.date}-broadcast-retrospective.json"
    if not args.dry_run:
        write_log(log_path, payload)
    payload["log"] = str(log_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
