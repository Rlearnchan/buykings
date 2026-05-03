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


def default_local_transcript_path(target_date: str) -> Path | None:
    mmdd = datetime.fromisoformat(target_date).strftime("%m%d")
    for suffix in ("rtf", "txt", "md"):
        matches = sorted(PROJECT_ROOT.glob(f"*{mmdd}*.{suffix}"))
        if matches:
            return matches[0]
    return None


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
    parser.add_argument("--ppt", type=Path)
    parser.add_argument("--local-transcript", type=Path)
    parser.add_argument("--skip-ppt-outline", action="store_true")
    parser.add_argument("--skip-actual-outline", action="store_true")
    parser.add_argument("--skip-asset-comparison", action="store_true")
    parser.add_argument("--skip-retrospective", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    py = args.python
    started_at = now_kst()
    operation = resolve_operation(args.date, calendar_path=args.broadcast_calendar, requested_mode=args.operation_mode)
    local_transcript = args.local_transcript or default_local_transcript_path(args.date)
    log_path = PROJECT_ROOT / "runtime" / "logs" / f"{args.date}-broadcast-retrospective.json"
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
        if not args.dry_run:
            write_log(
                log_path,
                {
                    "ok": True,
                    "date": args.date,
                    "started_at": started_at,
                    "ended_at": now_kst(),
                    "operation": operation,
                    "fetch": fetch_payload,
                    "retrospective": {"status": "pending"},
                    "steps": steps,
                    "phase": "fetch",
                },
            )
        if args.dry_run or fetch_payload.get("status") == "downloaded":
            break
        if attempt < args.attempts:
            sleep_seconds = max(0.0, args.sleep_minutes) * 60
            steps.append({"name": "sleep", "attempt": attempt, "payload": {"seconds": sleep_seconds}, "output_tail": ""})
            if not args.dry_run:
                write_log(
                    log_path,
                    {
                        "ok": True,
                        "date": args.date,
                        "started_at": started_at,
                        "ended_at": now_kst(),
                        "operation": operation,
                        "fetch": fetch_payload,
                        "retrospective": {"status": "pending"},
                        "steps": steps,
                        "phase": "sleep",
                    },
                )
            time.sleep(sleep_seconds)

    if not args.skip_ppt_outline:
        cmd = [py, "projects/autopark/scripts/extract_ppt_outline.py", "--date", args.date]
        if args.ppt:
            cmd.extend(["--ppt", str(args.ppt)])
        if args.dry_run:
            cmd.append("--dry-run")
        outline_payload, output = run(cmd, 120, allow_fail=True)
        steps.append({"name": "extract ppt outline", "optional": True, "payload": outline_payload, "output_tail": output[-1200:]})
    else:
        steps.append({"name": "extract ppt outline", "optional": True, "payload": {"status": "skipped"}, "output_tail": ""})

    if not args.skip_actual_outline:
        cmd = [py, "projects/autopark/scripts/build_actual_broadcast_outline.py", "--date", args.date]
        if local_transcript:
            cmd.extend(["--transcript", str(local_transcript)])
        if args.dry_run:
            cmd.append("--dry-run")
        actual_payload, output = run(cmd, 120, allow_fail=True)
        steps.append({"name": "build actual broadcast outline", "optional": True, "payload": actual_payload, "output_tail": output[-1200:]})
    else:
        steps.append({"name": "build actual broadcast outline", "optional": True, "payload": {"status": "skipped"}, "output_tail": ""})

    if not args.skip_asset_comparison:
        cmd = [py, "projects/autopark/scripts/compare_dashboard_to_broadcast_assets.py", "--date", args.date]
        if args.dry_run:
            cmd.append("--dry-run")
        comparison_payload, output = run(cmd, 120, allow_fail=True)
        steps.append({"name": "compare dashboard to broadcast assets", "optional": True, "payload": comparison_payload, "output_tail": output[-1200:]})
    else:
        steps.append({"name": "compare dashboard to broadcast assets", "optional": True, "payload": {"status": "skipped"}, "output_tail": ""})

    can_review = args.dry_run or fetch_payload.get("status") == "downloaded" or bool(local_transcript)
    if not args.skip_retrospective and can_review:
        cmd = [py, "projects/autopark/scripts/build_broadcast_retrospective.py", "--date", args.date]
        if local_transcript:
            cmd.extend(["--transcript", str(local_transcript)])
        if args.dry_run:
            cmd.append("--dry-run")
        review_payload, output = run(cmd, 180, allow_fail=True)
        steps.append({"name": "build broadcast retrospective", "payload": review_payload, "output_tail": output[-1200:]})
    else:
        steps.append({"name": "build broadcast retrospective", "payload": {"status": "skipped"}, "output_tail": ""})

    payload = {
        "ok": not any(step.get("payload", {}).get("ok") is False and not step.get("optional") for step in steps),
        "date": args.date,
        "started_at": started_at,
        "ended_at": now_kst(),
        "operation": operation,
        "local_transcript": str(local_transcript) if local_transcript else "",
        "fetch": fetch_payload,
        "retrospective": review_payload,
        "steps": steps,
    }
    if not args.dry_run:
        write_log(log_path, payload)
    payload["log"] = str(log_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
