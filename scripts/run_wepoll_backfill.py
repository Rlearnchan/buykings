#!/usr/bin/env python3
"""Backfill Wepoll daily index rows from archived raw CSVs, then optionally publish charts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from datetime import timedelta
from pathlib import Path

import run_wepoll_daily_append as daily_append


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOWNLOAD_DIR = ROOT / "runtime" / "downloads" / "wepoll"
DATE_COLUMNS = ("작성시각", "?묒꽦?쒓컖")


def set_csv_field_limit() -> None:
    for limit in (sys.maxsize, 2_147_483_647, 1_000_000_000):
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            continue


@dataclass(frozen=True)
class SourceCsv:
    path: Path
    counts: dict[str, int]
    mtime: float


def daterange(start: str, end: str) -> list[str]:
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)
    days: list[str] = []
    while current <= last:
        days.append(str(current))
        current += timedelta(days=1)
    return days


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def count_dates(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            day = (row.get("작성시각") or "")[:10]
            if not day:
                day = next(((row.get(column) or "")[:10] for column in DATE_COLUMNS if row.get(column)), "")
            if day:
                counts[day] = counts.get(day, 0) + 1
    return counts


def load_sources(download_dir: Path) -> list[SourceCsv]:
    set_csv_field_limit()
    sources: list[SourceCsv] = []
    for path in sorted(download_dir.glob("*.csv")):
        counts = count_dates(path)
        if counts:
            sources.append(SourceCsv(path=path.resolve(), counts=counts, mtime=path.stat().st_mtime))
    return sources


def choose_sources(sources: list[SourceCsv], days: list[str]) -> tuple[dict[str, SourceCsv], list[str]]:
    selected: dict[str, SourceCsv] = {}
    missing: list[str] = []
    for day in days:
        candidates = [source for source in sources if source.counts.get(day, 0) > 0]
        if not candidates:
            missing.append(day)
            continue
        selected[day] = max(candidates, key=lambda source: (source.counts[day], source.mtime))
    return selected, missing


def load_state_dates(state_dir: Path) -> set[str]:
    timeseries = state_dir / "appended_timeseries.csv"
    if not timeseries.exists():
        return set()
    with timeseries.open(encoding="utf-8", newline="") as handle:
        return {row["date"] for row in csv.DictReader(handle) if row.get("date")}


def redact_command(cmd: list[str]) -> list[str]:
    redacted: list[str] = []
    skip_next = False
    for part in cmd:
        if skip_next:
            redacted.append("<redacted>")
            skip_next = False
            continue
        redacted.append(part)
        if part in {"--openai-api-key", "--api-key", "--token"}:
            skip_next = True
    return redacted


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    if completed.returncode != 0:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "failed_command": redact_command(cmd),
                    "returncode": completed.returncode,
                    "output_tail": output[-4000:],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if output:
        print(output)
    return output


def publish_chart(spec_path: Path, python_executable: str, env_file: Path) -> dict:
    env = os.environ.copy()
    for key, value in load_env_file(env_file).items():
        env.setdefault(key, value)
    output = run([python_executable, "scripts/datawrapper_publish.py", str(spec_path)], env=env)
    try:
        return json.loads(output[output.find("{") :])
    except Exception:
        return {"spec": str(spec_path), "output_tail": output[-1200:]}


def validate_state(state_dir: Path, expected_days: list[str]) -> dict:
    timeseries = state_dir / "appended_timeseries.csv"
    rows = []
    with timeseries.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    dates = [row["date"] for row in rows]
    duplicates = sorted({day for day in dates if dates.count(day) > 1})
    missing = [day for day in expected_days if day not in set(dates)]
    if duplicates or missing or not dates or dates[-1] < expected_days[-1]:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "state_validation_failed",
                    "last_date": dates[-1] if dates else None,
                    "missing": missing,
                    "duplicates": duplicates,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return {"last_date": dates[-1], "row_count": len(rows), "missing": missing, "duplicates": duplicates}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--download-dir", type=Path, default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--state-dir", type=Path, default=daily_append.DEFAULT_STATE_DIR)
    parser.add_argument("--timeseries-spec", type=Path, default=daily_append.DEFAULT_TIMESERIES_SPEC)
    parser.add_argument("--bubble-spec", type=Path, default=daily_append.DEFAULT_BUBBLE_SPEC)
    parser.add_argument("--panic-root", type=Path)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--model", default=os.environ.get("WEPOLL_SECOND_PASS_MODEL"))
    parser.add_argument("--second-pass-backend", default=os.environ.get("WEPOLL_SECOND_PASS_BACKEND"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--inventory-only", action="store_true", help="Inspect raw CSV coverage and exit before computing")
    args = parser.parse_args()
    env_values = load_env_file(args.env_file.resolve())
    panic_root = args.panic_root or (
        Path(env_values["WEPOLL_PANIC_ROOT"]) if env_values.get("WEPOLL_PANIC_ROOT") else daily_append.DEFAULT_PANIC_ROOT
    )
    model = args.model or env_values.get("WEPOLL_SECOND_PASS_MODEL") or "gemma3:4b"
    second_pass_backend = args.second_pass_backend or env_values.get("WEPOLL_SECOND_PASS_BACKEND") or "ollama"
    openai_api_key = args.openai_api_key or env_values.get("OPENAI_API_KEY")
    if openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", openai_api_key)

    expected_days = daterange(args.start_date, args.end_date)
    sources = load_sources(args.download_dir.resolve())
    selected, missing = choose_sources(sources, expected_days)
    if args.inventory_only:
        print(
            json.dumps(
                {
                    "ok": not missing,
                    "start_date": args.start_date,
                    "end_date": args.end_date,
                    "missing": missing,
                    "selected": {
                        day: {"path": str(source.path), "rows": source.counts[day]}
                        for day, source in selected.items()
                    },
                    "inventory": [
                        {"path": str(source.path), "counts": source.counts}
                        for source in sources
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    already_done = load_state_dates(args.state_dir.resolve())
    missing_to_process = [day for day in missing if day not in already_done]
    if missing_to_process:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "error": "missing_raw_csv_for_dates",
                    "missing": missing_to_process,
                    "download_dir": str(args.download_dir.resolve()),
                    "inventory": [
                        {"path": str(source.path), "counts": source.counts}
                        for source in sources
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    processed: list[dict[str, object]] = []
    for day in expected_days:
        if day in already_done:
            processed.append({"date": day, "status": "already_in_state"})
            continue
        source = selected[day]
        command = [
            args.python_executable,
            "scripts/run_wepoll_daily_append.py",
            "--input",
            str(source.path),
            "--target-date",
            day,
            "--skip-publish",
            "--state-dir",
            str(args.state_dir.resolve()),
            "--timeseries-spec",
            str(args.timeseries_spec.resolve()),
            "--bubble-spec",
            str(args.bubble_spec.resolve()),
            "--panic-root",
            str(panic_root.resolve()),
            "--python-executable",
            args.python_executable,
            "--model",
            model,
            "--second-pass-backend",
            second_pass_backend,
            "--ollama-host",
            args.ollama_host,
            "--env-file",
            str(args.env_file.resolve()),
        ]
        run(command)
        processed.append({"date": day, "status": "processed", "source": str(source.path), "rows": source.counts[day]})
        already_done.add(day)

    daily_append.update_chart_specs(args.timeseries_spec.resolve(), args.bubble_spec.resolve())
    validation = validate_state(args.state_dir.resolve(), expected_days)

    publish_results: list[dict] = []
    if args.publish:
        publish_results.append(publish_chart(args.timeseries_spec.resolve(), args.python_executable, args.env_file.resolve()))
        publish_results.append(publish_chart(args.bubble_spec.resolve(), args.python_executable, args.env_file.resolve()))

    print(
        json.dumps(
            {
                "ok": True,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "processed": processed,
                "validation": validation,
                "published": bool(args.publish),
                "publish_results": publish_results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
