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


def set_csv_field_limit() -> None:
    for limit in (sys.maxsize, 2_147_483_647, 1_000_000_000):
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            continue


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
    set_csv_field_limit()
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
    set_csv_field_limit()
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
        candidate = datetime.strptime(required_market_date, "%Y-%m-%d").date()
        for _ in range(10):
            try:
                run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / "fetch_investing_historical.py"),
                        "--preset",
                        preset,
                        "--output",
                        str(output),
                        "--required-date",
                        str(candidate),
                    ]
                )
                break
            except subprocess.CalledProcessError:
                candidate -= timedelta(days=1)
                while candidate.weekday() >= 5:
                    candidate -= timedelta(days=1)
        else:
            raise SystemExit(f"Could not fetch market data for {preset} near {target_date}")
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
    baseline_market: Path,
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


def date_label(value: str) -> str:
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y.%m.%d")


def next_day(value: str) -> str:
    return str(datetime.strptime(value, "%Y-%m-%d").date() + timedelta(days=1))


def update_timeseries_spec(spec_path: Path, prepared_csv: Path) -> None:
    rows = load_rows(prepared_csv)
    if not rows:
        return
    start_date = rows[0]["date"]
    end_date = rows[-1]["date"]
    week_start, _ = week_bounds(end_date)
    spec = read_json(spec_path)
    metadata = spec.setdefault("metadata", {})
    metadata.setdefault("annotate", {})["notes"] = (
        f"분석 기간: {date_label(start_date)} ~ {date_label(end_date)}, "
        "지수는 50(중립)을 기준으로 해석"
    )
    visualize = metadata.setdefault("visualize", {})
    for annotation in visualize.get("range-annotations", []) or []:
        position = annotation.get("position") or {}
        if annotation.get("type") == "y":
            position["x0"] = f"{start_date} 00:00"
            position["x1"] = f"{end_date} 00:00"
        elif annotation.get("type") == "x":
            position["x0"] = f"{week_start} 00:00"
            position["x1"] = f"{next_day(end_date)} 00:00"
        annotation["position"] = position
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_bubble_spec(spec_path: Path, prepared_csv: Path) -> None:
    rows = load_rows(prepared_csv)
    if not rows:
        return
    start_date = rows[0]["date"]
    end_date = rows[-1]["date"]
    spec = read_json(spec_path)
    metadata = spec.setdefault("metadata", {})
    metadata.setdefault("annotate", {})["notes"] = (
        f"분석 기간: {date_label(start_date)} ~ {date_label(end_date)}, "
        "순서는 해당 주 1일차부터 최신 일차까지"
    )
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_chart_specs(timeseries_spec: Path, bubble_spec: Path) -> None:
    update_timeseries_spec(timeseries_spec, resolve_prepared_csv(timeseries_spec))
    update_bubble_spec(bubble_spec, resolve_prepared_csv(bubble_spec))


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
    parser.add_argument("--model", default=None)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--timeseries-spec", type=Path, default=DEFAULT_TIMESERIES_SPEC)
    parser.add_argument("--bubble-spec", type=Path, default=DEFAULT_BUBBLE_SPEC)
    parser.add_argument("--panic-root", type=Path)
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--second-pass-backend", default=os.environ.get("WEPOLL_SECOND_PASS_BACKEND"))
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--skip-publish", action="store_true")
    args = parser.parse_args()
    env_values = load_env_file(args.env_file.resolve())
    panic_root = args.panic_root or (
        Path(env_values["WEPOLL_PANIC_ROOT"]) if env_values.get("WEPOLL_PANIC_ROOT") else DEFAULT_PANIC_ROOT
    )
    model = args.model or env_values.get("WEPOLL_SECOND_PASS_MODEL") or "gemma3:4b"
    second_pass_backend = args.second_pass_backend or env_values.get("WEPOLL_SECOND_PASS_BACKEND") or "ollama"
    openai_api_key = args.openai_api_key or env_values.get("OPENAI_API_KEY")

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
        model,
        panic_root=panic_root.resolve(),
        python_executable=args.python_executable,
        second_pass_backend=second_pass_backend,
        ollama_host=args.ollama_host,
        openai_api_key=openai_api_key,
    )
    baseline_market = panic_root.resolve() / "output" / "yearly_hybrid_batch_v4" / "market_daily_normalized.csv"
    outputs = append_state(args.state_dir, features_path, market_paths, target_date, baseline_market)

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
    update_chart_specs(args.timeseries_spec, args.bubble_spec)

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
                "panic_root": str(panic_root),
                "published": not args.skip_publish,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
