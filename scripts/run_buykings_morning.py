#!/usr/bin/env python3
"""Run top-level Buykings morning jobs from a manifest."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "buykings-morning.json"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def run_job(job: dict) -> dict:
    if job.get("kind") != "command":
        return {
            "id": job["id"],
            "kind": job.get("kind"),
            "status": "skipped",
            "reason": "non-command job",
        }

    command = job.get("command") or []
    if not command:
        raise SystemExit(f"Job has no command: {job['id']}")

    resolved_command = list(command)
    if resolved_command and resolved_command[0] in {"python", "python3"}:
        # Reuse the current interpreter so the manifest stays portable on Windows.
        resolved_command[0] = sys.executable

    completed = subprocess.run(
        resolved_command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    result = {
        "id": job["id"],
        "kind": job["kind"],
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "command": resolved_command,
    }
    if completed.stdout:
        result["stdout"] = completed.stdout.strip()
    if completed.stderr:
        result["stderr"] = completed.stderr.strip()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--job", action="append", help="Run only the specified job id; repeatable")
    parser.add_argument("--list", action="store_true", help="List configured jobs and exit")
    args = parser.parse_args()

    config = load_config(args.config.resolve())
    jobs = config.get("jobs", [])

    if args.list:
        print(
            json.dumps(
                [
                    {
                        "id": job["id"],
                        "enabled": job.get("enabled", False),
                        "kind": job.get("kind"),
                        "description": job.get("description", ""),
                    }
                    for job in jobs
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    selected = set(args.job or [])
    runnable: list[dict] = []
    for job in jobs:
        if not job.get("enabled", False):
            continue
        if selected and job["id"] not in selected:
            continue
        runnable.append(job)

    if not runnable:
        raise SystemExit("No enabled jobs matched the request.")

    results = [run_job(job) for job in runnable]
    payload = {
        "ok": all(result["status"] == "ok" for result in results),
        "name": config.get("name", "buykings-morning"),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
