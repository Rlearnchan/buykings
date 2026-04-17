#!/usr/bin/env python3
"""Run one-day Wepoll append flow from raw posts CSV to Datawrapper publish."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANIC_ROOT = ROOT.parent / "wepoll-panic"
DEFAULT_STATE_DIR = ROOT / "projects" / "wepoll-panic" / "state"
DEFAULT_TIMESERIES_SPEC = ROOT / "projects" / "wepoll-panic" / "charts" / "weekly-timeseries-2026-04-15-datawrapper.json"
DEFAULT_BUBBLE_SPEC = ROOT / "projects" / "wepoll-panic" / "charts" / "weekly-bubble-2026-04-15-datawrapper.json"
DEFAULT_BASELINE_MARKET = PANIC_ROOT / "output" / "yearly_hybrid_batch_v4" / "market_daily_normalized.csv"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def resolve_prepared_csv(spec_path: Path) -> Path:
    spec = read_json(spec_path)
    raw = spec["prepared_csv"]
    path = Path(raw)
    return path if path.is_absolute() else (spec_path.parent / path).resolve()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def load_date_counts(path: Path) -> Counter[str]:
    csv.field_size_limit(sys.maxsize)
    counts: Counter[str] = Counter()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            counts[(row.get("작성시각") or "")[:10]] += 1
    return counts


def choose_target_date(counts: Counter[str], today: date, min_rows: int) -> str:
    candidates = [
        day for day, count in counts.items()
        if day and day < str(today) and count >= min_rows
    ]
    if not candidates:
        raise SystemExit(
            f"No complete Wepoll date found before {today} with at least {min_rows} rows."
        )
    return max(candidates)


def filter_csv_for_date(src: Path, dst: Path, target_date: str) -> int:
    csv.field_size_limit(sys.maxsize)
    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    with src.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if (row.get("작성시각") or "")[:10] == target_date:
                rows.append(row)
    if not rows or not fieldnames:
        raise SystemExit(f"No rows found for target date: {target_date}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def fetch_market(target_date: str, workdir: Path) -> dict[str, Path]:
    outputs = {}
    for preset in ["kospi", "kosdaq", "vkospi"]:
        output = workdir / f"{preset}.csv"
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "fetch_investing_historical.py"),
                "--preset",
                preset,
                "--output",
                str(output),
                "--required-date",
                target_date,
            ]
        )
        outputs[preset] = output
    return outputs


def run_daily_batch(target_date_csv: Path, market_paths: dict[str, Path], pipeline_dir: Path, model: str) -> Path:
    env = os.environ.copy()
    env.update(
        {
            "WORKDIR": str(pipeline_dir),
            "WEPOLL_EXPORT": str(target_date_csv),
            "KOSPI_CSV": str(market_paths["kospi"]),
            "KOSDAQ_CSV": str(market_paths["kosdaq"]),
            "VKOSPI_CSV": str(market_paths["vkospi"]),
            "MODEL": model,
        }
    )
    features_path = pipeline_dir / "calibration_daily_features.csv"
    try:
        run(["zsh", str(PANIC_ROOT / "scripts" / "run_daily_server_batch.sh")], env=env)
    except subprocess.CalledProcessError:
        if not features_path.exists():
            raise
    return features_path


def append_state(
    state_dir: Path,
    new_features: Path,
    market_paths: dict[str, Path],
    target_date: str,
) -> dict[str, Path]:
    outputs = {
        "stance": state_dir / "appended_stance.csv",
        "quadrant": state_dir / "appended_quadrant.csv",
        "timeseries": state_dir / "appended_timeseries.csv",
        "bubble": state_dir / "appended_bubble.csv",
        "ranges": state_dir / "appended_ranges.csv",
    }
    current_timeseries = state_dir / "appended_timeseries.csv"
    if not current_timeseries.exists():
        raise SystemExit(f"Missing state file: {current_timeseries}")
    run(
        [
            sys.executable,
            str(ROOT / "scripts" / "append_weekly_marketblend.py"),
            "--old-stance",
            str(state_dir / "appended_stance.csv"),
            "--new-features",
            str(new_features),
            "--timeseries-old",
            str(state_dir / "appended_timeseries.csv"),
            "--market-kospi",
            str(market_paths["kospi"]),
            "--market-kosdaq",
            str(market_paths["kosdaq"]),
            "--market-vkospi",
            str(market_paths["vkospi"]),
            "--market-existing",
            str(DEFAULT_BASELINE_MARKET),
            "--end-date",
            target_date,
            "--output-stance",
            str(outputs["stance"]),
            "--output-quadrant",
            str(outputs["quadrant"]),
            "--output-timeseries",
            str(outputs["timeseries"]),
            "--output-bubble",
            str(outputs["bubble"]),
            "--output-ranges",
            str(outputs["ranges"]),
        ]
    )
    return outputs


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_prepared_timeseries(appended_timeseries: Path, undated_path: Path, dated_path: Path | None) -> None:
    rows = load_rows(appended_timeseries)[-42:]
    out = []
    for idx, row in enumerate(rows, start=1):
        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        out.append(
            {
                "plot_seq": str(idx),
                "date": row["date"],
                "display_date": f"{dt.month}/{dt.day}",
                "state_label_ko": row["state_label_ko"],
                "psychology_index_0_100": f"{float(row['psychology_index_0_100']):.2f}",
                "participation_index_0_100": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": str(int(float(row["post_count"]))),
            }
        )
    fieldnames = ["plot_seq", "date", "display_date", "state_label_ko", "psychology_index_0_100", "participation_index_0_100", "post_count"]
    write_rows(undated_path, out, fieldnames)
    if dated_path:
        write_rows(dated_path, out, fieldnames)


def update_prepared_ranges(timeseries_path: Path, undated_path: Path, dated_path: Path | None) -> None:
    rows = load_rows(timeseries_path)
    ranges = []
    current_state = None
    start_date = None
    prev_date = None
    for row in rows:
        if row["state_label_ko"] != current_state:
            if current_state is not None:
                ranges.append({"state_label_ko": current_state, "start_date": start_date, "end_date": prev_date})
            current_state = row["state_label_ko"]
            start_date = row["date"]
        prev_date = row["date"]
    if current_state is not None:
        ranges.append({"state_label_ko": current_state, "start_date": start_date, "end_date": prev_date})
    fieldnames = ["state_label_ko", "start_date", "end_date"]
    write_rows(undated_path, ranges, fieldnames)
    if dated_path:
        write_rows(dated_path, ranges, fieldnames)


def week_bounds(target_date: str) -> tuple[str, str]:
    current = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = current - timedelta(days=current.weekday())
    end = start + timedelta(days=6)
    return str(start), str(end)


def update_prepared_bubble(appended_quadrant: Path, target_date: str, undated_path: Path, dated_path: Path | None) -> None:
    start, end = week_bounds(target_date)
    rows_by_date = {row["date"]: row for row in load_rows(appended_quadrant)}
    selected_dates = sorted(day for day in rows_by_date if start <= day <= target_date)
    out = []
    for idx, day in enumerate(selected_dates, start=1):
        row = rows_by_date[day]
        out.append(
            {
                "day_seq": str(idx),
                "day_label": f"{idx}일차",
                "date": day,
                "week_range": f"{start}~{end}",
                "state_label_ko": row["state_label_ko"],
                "심리(Bear-Bull) 지수": f"{float(row['stance_index_0_100']):.2f}",
                "참여 지수": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": str(int(float(row["post_count"]))),
            }
        )
    fieldnames = ["day_seq", "day_label", "date", "week_range", "state_label_ko", "심리(Bear-Bull) 지수", "참여 지수", "post_count"]
    write_rows(undated_path, out, fieldnames)
    if dated_path:
        write_rows(dated_path, out, fieldnames)


def publish(spec_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    run(["zsh", "-lc", f"set -a; source .env; python3 scripts/datawrapper_publish.py {spec_path}"], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Raw Wepoll CSV")
    parser.add_argument("--target-date", help="Append this date explicitly (YYYY-MM-DD)")
    parser.add_argument("--min-rows", type=int, default=150, help="Minimum rows to treat a date as complete when auto-selecting")
    parser.add_argument("--today", default=str(date.today()), help="Override today's date for auto-selection")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--timeseries-spec", type=Path, default=DEFAULT_TIMESERIES_SPEC)
    parser.add_argument("--bubble-spec", type=Path, default=DEFAULT_BUBBLE_SPEC)
    parser.add_argument("--skip-publish", action="store_true")
    args = parser.parse_args()

    counts = load_date_counts(args.input)
    target_date = args.target_date or choose_target_date(counts, date.fromisoformat(args.today), args.min_rows)

    workdir = ROOT / "tmp" / f"wepoll_daily_append_{target_date}"
    workdir.mkdir(parents=True, exist_ok=True)

    filtered_csv = workdir / f"wepoll_stock_posts_{target_date}.csv"
    row_count = filter_csv_for_date(args.input, filtered_csv, target_date)
    market_paths = fetch_market(target_date, workdir)
    features_path = run_daily_batch(filtered_csv, market_paths, workdir / "pipeline", args.model)
    outputs = append_state(args.state_dir, features_path, market_paths, target_date)

    timeseries_dated = resolve_prepared_csv(args.timeseries_spec)
    bubble_dated = resolve_prepared_csv(args.bubble_spec)
    prepared_dir = timeseries_dated.parent
    timeseries_undated = prepared_dir / "dw_weekly_timeseries_recent6w.csv"
    ranges_undated = prepared_dir / "dw_weekly_timeseries_state_ranges_recent6w.csv"
    bubble_undated = prepared_dir / "dw_weekly_bubble_latest_week.csv"
    ranges_dated = prepared_dir / timeseries_dated.name.replace("dw_weekly_timeseries_recent6w", "dw_weekly_timeseries_state_ranges_recent6w")

    update_prepared_timeseries(outputs["timeseries"], timeseries_undated, timeseries_dated)
    update_prepared_ranges(timeseries_dated, ranges_undated, ranges_dated)
    update_prepared_bubble(outputs["quadrant"], target_date, bubble_undated, bubble_dated)

    if not args.skip_publish:
        publish(args.timeseries_spec)
        publish(args.bubble_spec)

    print(
        json.dumps(
            {
                "ok": True,
                "target_date": target_date,
                "row_count": row_count,
                "state_dir": str(args.state_dir),
                "timeseries_spec": str(args.timeseries_spec),
                "bubble_spec": str(args.bubble_spec),
                "published": not args.skip_publish,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
