from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def set_csv_field_limit() -> None:
    for limit in (sys.maxsize, 2_147_483_647, 1_000_000_000):
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            continue


def find_buykings_root() -> Path:
    env_root = os.environ.get("BUYKINGS_ROOT")
    if env_root:
        root = Path(env_root).resolve()
        if (root / "scripts" / "run_wepoll_panic_daily_batch.py").exists():
            return root
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "scripts" / "run_wepoll_panic_daily_batch.py").exists():
            return candidate
    raise SystemExit("Could not locate buykings root. Set BUYKINGS_ROOT.")


def find_panic_root(buykings_root: Path) -> Path:
    candidates = [
        os.environ.get("WEPOLL_PANIC_ROOT"),
        str(buykings_root / "vendor" / "wepoll-panic"),
        str(buykings_root.parent / "wepoll-panic"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw).resolve()
        if (path / "src" / "wepoll_fear_index").exists():
            return path
    raise SystemExit("Could not locate wepoll-panic source. Set WEPOLL_PANIC_ROOT.")


def filter_posts_for_date(src: Path, dst: Path, target_date: str) -> int:
    set_csv_field_limit()
    with src.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [row for row in reader if (row.get("작성시각") or "")[:10] == target_date]
    if not rows:
        raise SystemExit(f"No Wepoll rows found for {target_date}.")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def read_result(timeseries_path: Path, target_date: str, output: Path) -> dict:
    with timeseries_path.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("date") == target_date]
    if not rows:
        raise SystemExit(f"Computed timeseries does not include {target_date}: {timeseries_path}")
    row = rows[-1]
    payload = {
        "date": row["date"],
        "state_label_ko": row["state_label_ko"],
        "psychology_index_0_100": float(row["psychology_index_0_100"]),
        "participation_index_0_100": float(row["participation_index_0_100"]),
        "post_count": int(float(row["post_count"])),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def compute(args: argparse.Namespace) -> None:
    buykings_root = find_buykings_root()
    panic_root = find_panic_root(buykings_root)
    state_dir = args.state.resolve()
    baseline_market = Path(
        os.environ.get(
            "WEPOLL_MARKET_BASELINE",
            str(panic_root / "output" / "yearly_hybrid_batch_v4" / "market_daily_normalized.csv"),
        )
    ).resolve()

    with tempfile.TemporaryDirectory(prefix=f"wepoll-index-{args.date}-") as tmp:
        workdir = Path(tmp)
        filtered_posts = workdir / f"posts-{args.date}.csv"
        row_count = filter_posts_for_date(args.posts.resolve(), filtered_posts, args.date)
        pipeline_dir = workdir / "pipeline"
        outputs_dir = workdir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        daily_batch_cmd = [
                sys.executable,
                str(buykings_root / "scripts" / "run_wepoll_panic_daily_batch.py"),
                "--panic-root",
                str(panic_root),
                "--python-executable",
                sys.executable,
                "--workdir",
                str(pipeline_dir),
                "--wepoll-export",
                str(filtered_posts),
                "--kospi-csv",
                str(args.kospi.resolve()),
                "--kosdaq-csv",
                str(args.kosdaq.resolve()),
                "--vkospi-csv",
                str(args.vkospi.resolve()),
                "--model",
                os.environ.get("WEPOLL_SECOND_PASS_MODEL", "gpt-5-mini"),
                "--second-pass-backend",
                os.environ.get("WEPOLL_SECOND_PASS_BACKEND", "openai"),
                "--ollama-host",
                os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
        ]
        try:
            run(daily_batch_cmd)
        except subprocess.CalledProcessError:
            features_path = pipeline_dir / "calibration_daily_features.csv"
            if not features_path.exists():
                raise

        run(
            [
                sys.executable,
                str(buykings_root / "scripts" / "append_weekly_marketblend.py"),
                "--old-stance",
                str(state_dir / "appended_stance.csv"),
                "--new-features",
                str(pipeline_dir / "calibration_daily_features.csv"),
                "--timeseries-old",
                str(state_dir / "appended_timeseries.csv"),
                "--market-kospi",
                str(args.kospi.resolve()),
                "--market-kosdaq",
                str(args.kosdaq.resolve()),
                "--market-vkospi",
                str(args.vkospi.resolve()),
                "--market-existing",
                str(baseline_market),
                "--end-date",
                args.date,
                "--output-stance",
                str(outputs_dir / "appended_stance.csv"),
                "--output-quadrant",
                str(outputs_dir / "appended_quadrant.csv"),
                "--output-timeseries",
                str(outputs_dir / "appended_timeseries.csv"),
                "--output-bubble",
                str(outputs_dir / "appended_bubble.csv"),
                "--output-ranges",
                str(outputs_dir / "appended_ranges.csv"),
            ]
        )

        payload = read_result(outputs_dir / "appended_timeseries.csv", args.date, args.output.resolve())
        payload["post_count"] = row_count if payload["post_count"] == 0 else payload["post_count"]
        args.output.resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.output.resolve()), "result": payload}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="wepoll-index")
    subparsers = parser.add_subparsers(dest="command", required=True)
    compute_parser = subparsers.add_parser("compute", help="Compute one Wepoll index row")
    compute_parser.add_argument("--posts", required=True, type=Path)
    compute_parser.add_argument("--kospi", required=True, type=Path)
    compute_parser.add_argument("--kosdaq", required=True, type=Path)
    compute_parser.add_argument("--vkospi", required=True, type=Path)
    compute_parser.add_argument("--state", required=True, type=Path)
    compute_parser.add_argument("--date", required=True)
    compute_parser.add_argument("--output", required=True, type=Path)
    compute_parser.set_defaults(func=compute)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
