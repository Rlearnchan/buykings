#!/usr/bin/env python3
"""Run one-day Wepoll append flow from raw posts CSV to Datawrapper publish."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PANIC_ROOT = Path(
    os.environ.get("WEPOLL_PANIC_ROOT", str((ROOT.parent / "wepoll-panic").resolve()))
).resolve()
DEFAULT_STATE_DIR = ROOT / "projects" / "wepoll-panic" / "state"
DEFAULT_TIMESERIES_SPEC = ROOT / "projects" / "wepoll-panic" / "charts" / "weekly-timeseries-2026-04-15-datawrapper.json"
DEFAULT_BUBBLE_SPEC = ROOT / "projects" / "wepoll-panic" / "charts" / "weekly-bubble-2026-04-15-datawrapper.json"
DEFAULT_BASELINE_MARKET = DEFAULT_PANIC_ROOT / "output" / "yearly_hybrid_batch_v4" / "market_daily_normalized.csv"


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def resolve_prepared_csv(spec_path: Path) -> Path:
    spec = read_json(spec_path)
    raw = spec["prepared_csv"]
    path = Path(raw)
    return path if path.is_absolute() else (spec_path.parent / path).resolve()


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def format_date_ko(value: str) -> str:
    dt = datetime.strptime(value, "%Y-%m-%d")
    return f"{dt.year:04d}.{dt.month:02d}.{dt.day:02d}"


def next_monday(value: str) -> str:
    dt = datetime.strptime(value, "%Y-%m-%d") + timedelta(days=7)
    return dt.strftime("%Y-%m-%d")


def latest_matching_spec(charts_dir: Path, prefix: str) -> Path:
    matches = sorted(charts_dir.glob(f"{prefix}-*.json"))
    if not matches:
        raise SystemExit(f"Missing chart spec templates for prefix: {prefix}")
    return matches[-1]


def ensure_weekly_spec(
    *,
    charts_dir: Path,
    prefix: str,
    week_start: str,
    prepared_csv_name: str,
) -> Path:
    spec_path = charts_dir / f"{prefix}-{week_start}.json"
    if spec_path.exists():
        return spec_path

    template_path = latest_matching_spec(charts_dir, prefix)
    spec = read_json(template_path)
    spec["slug"] = f"{prefix}-{week_start}"
    spec["prepared_csv"] = f"../prepared/{prepared_csv_name}"
    spec.pop("chart_id", None)
    write_json(spec_path, spec)
    return spec_path


def sync_timeseries_spec(spec_path: Path, prepared_csv_path: Path, week_start: str) -> None:
    spec = read_json(spec_path)
    rows = load_rows(prepared_csv_path)
    if not rows:
        return

    first_date = rows[0]["date"]
    last_date = rows[-1]["date"]
    note = f"분석 기간: {format_date_ko(first_date)} ~ {format_date_ko(last_date)}, 지수는 50(점선)을 기준으로 해석"

    metadata = spec.setdefault("metadata", {})
    annotate = metadata.setdefault("annotate", {})
    annotate["notes"] = note

    visualize = metadata.setdefault("visualize", {})
    annotations = visualize.get("range-annotations", [])
    for annotation in annotations:
        position = annotation.get("position", {})
        if annotation.get("type") == "y":
            position["x0"] = f"{first_date} 00:00"
            position["x1"] = f"{last_date} 00:00"
        elif annotation.get("type") == "x" and annotation.get("display") == "range":
            position["x0"] = f"{week_start} 00:00"
            position["x1"] = f"{next_monday(week_start)} 00:00"

    write_json(spec_path, spec)


def sync_bubble_spec(spec_path: Path, prepared_csv_path: Path, week_start: str, target_date: str) -> None:
    spec = read_json(spec_path)
    if not prepared_csv_path.exists():
        return

    end_date = min(target_date, (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d"))
    metadata = spec.setdefault("metadata", {})
    annotate = metadata.setdefault("annotate", {})
    annotate["notes"] = f"분석 기간: {format_date_ko(week_start)} ~ {format_date_ko(end_date)}, 순서대로 월(1)~일(7)"
    write_json(spec_path, spec)


def configure_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            # Windows can reject sys.maxsize when C long is smaller.
            limit //= 10


def load_date_counts(path: Path) -> Counter[str]:
    configure_csv_field_limit()
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
    configure_csv_field_limit()
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
    required_market_date = market_reference_date(target_date)
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
                required_market_date,
            ]
        )
        outputs[preset] = output
    return outputs


def market_reference_date(target_date: str) -> str:
    current = datetime.strptime(target_date, "%Y-%m-%d").date()
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return str(current)


def run_daily_batch(
    target_date_csv: Path,
    market_paths: dict[str, Path],
    pipeline_dir: Path,
    model: str,
    *,
    panic_root: Path,
    python_executable: str,
    second_pass_backend: str,
    ollama_host: str,
    openai_api_key: str | None,
) -> Path:
    features_path = pipeline_dir / "calibration_daily_features.csv"
    try:
        command = [
            python_executable,
            str(ROOT / "scripts" / "run_wepoll_panic_daily_batch.py"),
            "--panic-root",
            str(panic_root),
            "--python-executable",
            python_executable,
            "--workdir",
            str(pipeline_dir),
            "--wepoll-export",
            str(target_date_csv),
            "--kospi-csv",
            str(market_paths["kospi"]),
            "--kosdaq-csv",
            str(market_paths["kosdaq"]),
            "--vkospi-csv",
            str(market_paths["vkospi"]),
            "--model",
            model,
            "--second-pass-backend",
            second_pass_backend,
            "--ollama-host",
            ollama_host,
        ]
        if openai_api_key:
            command.extend(["--openai-api-key", openai_api_key])
        run(command)
    except subprocess.CalledProcessError as exc:
        # Daily additive only needs the merged daily features. The downstream
        # anchor-calibration step in the legacy batch script expects a wider
        # baseline window and can fail on a one-day slice, so we continue only
        # when the feature table was already produced.
        if not features_path.exists():
            raise
        print(
            (
                "warning: legacy anchor-calibration stage failed after daily "
                "features were created; continuing with append-only flow "
                f"using {features_path} (exit={exc.returncode})"
            ),
            file=sys.stderr,
        )
    if not features_path.exists():
        raise SystemExit(f"Missing daily features after batch run: {features_path}")
    return features_path


def append_state(
    state_dir: Path,
    new_features: Path,
    market_paths: dict[str, Path],
    target_date: str,
    panic_root: Path,
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
    baseline_market = panic_root / "output" / "yearly_hybrid_batch_v4" / "market_daily_normalized.csv"
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
            str(baseline_market),
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


def publish(spec_path: Path, *, env_file: Path, python_executable: str) -> None:
    env = os.environ.copy()
    for key, value in load_env_file(env_file).items():
        env.setdefault(key, value)
    env["PYTHONUNBUFFERED"] = "1"
    run([python_executable, str(ROOT / "scripts" / "datawrapper_publish.py"), str(spec_path)], env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Raw Wepoll CSV")
    parser.add_argument("--target-date", help="Append this date explicitly (YYYY-MM-DD)")
    parser.add_argument("--min-rows", type=int, default=150, help="Minimum rows to treat a date as complete when auto-selecting")
    parser.add_argument("--today", default=str(date.today()), help="Override today's date for auto-selection")
    parser.add_argument("--model", default=os.environ.get("WEPOLL_SECOND_PASS_MODEL", "gemma3:4b"))
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--timeseries-spec", type=Path, default=DEFAULT_TIMESERIES_SPEC)
    parser.add_argument("--bubble-spec", type=Path, default=DEFAULT_BUBBLE_SPEC)
    parser.add_argument("--panic-root", type=Path, default=DEFAULT_PANIC_ROOT)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--second-pass-backend", default=os.environ.get("WEPOLL_SECOND_PASS_BACKEND", "ollama"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--skip-publish", action="store_true")
    args = parser.parse_args()

    env_values = load_env_file(args.env_file)
    if args.panic_root == DEFAULT_PANIC_ROOT and env_values.get("WEPOLL_PANIC_ROOT"):
        args.panic_root = Path(env_values["WEPOLL_PANIC_ROOT"]).resolve()
    if args.second_pass_backend == os.environ.get("WEPOLL_SECOND_PASS_BACKEND", "ollama"):
        args.second_pass_backend = env_values.get("WEPOLL_SECOND_PASS_BACKEND", args.second_pass_backend)
    if args.model == os.environ.get("WEPOLL_SECOND_PASS_MODEL", "gemma3:4b"):
        args.model = env_values.get("WEPOLL_SECOND_PASS_MODEL", args.model)
    if args.ollama_host == os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"):
        args.ollama_host = env_values.get("OLLAMA_HOST", args.ollama_host)
    if not args.openai_api_key and env_values.get("OPENAI_API_KEY"):
        args.openai_api_key = env_values["OPENAI_API_KEY"]

    counts = load_date_counts(args.input)
    target_date = args.target_date or choose_target_date(counts, date.fromisoformat(args.today), args.min_rows)

    workdir = ROOT / "tmp" / f"wepoll_daily_append_{target_date}"
    workdir.mkdir(parents=True, exist_ok=True)

    filtered_csv = workdir / f"wepoll_stock_posts_{target_date}.csv"
    row_count = filter_csv_for_date(args.input, filtered_csv, target_date)
    market_paths = fetch_market(target_date, workdir)
    features_path = run_daily_batch(
        filtered_csv,
        market_paths,
        workdir / "pipeline",
        args.model,
        panic_root=args.panic_root.resolve(),
        python_executable=args.python_executable,
        second_pass_backend=args.second_pass_backend,
        ollama_host=args.ollama_host,
        openai_api_key=args.openai_api_key,
    )
    outputs = append_state(args.state_dir, features_path, market_paths, target_date, args.panic_root.resolve())

    charts_dir = args.state_dir.parent / "charts"
    week_start, _week_end = week_bounds(target_date)
    auto_timeseries_spec = ensure_weekly_spec(
        charts_dir=charts_dir,
        prefix="weekly-timeseries",
        week_start=week_start,
        prepared_csv_name=f"dw_weekly_timeseries_recent6w_{week_start}.csv",
    )
    auto_bubble_spec = ensure_weekly_spec(
        charts_dir=charts_dir,
        prefix="weekly-bubble",
        week_start=week_start,
        prepared_csv_name=f"dw_weekly_bubble_latest_week_{week_start}.csv",
    )
    args.timeseries_spec = auto_timeseries_spec
    args.bubble_spec = auto_bubble_spec

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
    sync_timeseries_spec(args.timeseries_spec, timeseries_dated, week_start)
    sync_bubble_spec(args.bubble_spec, bubble_dated, week_start, target_date)

    if not args.skip_publish:
        publish(args.timeseries_spec, env_file=args.env_file.resolve(), python_executable=args.python_executable)
        publish(args.bubble_spec, env_file=args.env_file.resolve(), python_executable=args.python_executable)

    print(
        json.dumps(
            {
                "ok": True,
                "target_date": target_date,
                "row_count": row_count,
                "state_dir": str(args.state_dir),
                "timeseries_spec": str(args.timeseries_spec),
                "bubble_spec": str(args.bubble_spec),
                "panic_root": str(args.panic_root),
                "published": not args.skip_publish,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
