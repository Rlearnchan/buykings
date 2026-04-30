#!/usr/bin/env python3
"""Prepare a Datawrapper-ready histogram CSV for weekly Wepoll post impact."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANIC_PREPARED_DIR = ROOT / "projects" / "wepoll-panic" / "prepared"

DEFAULT_INPUTS = [
    ROOT / "tmp" / "wepoll_weekly_2026-04-15" / "pipeline" / "final_merged.csv",
    ROOT / "tmp" / "wepoll_daily_append_2026-04-16" / "pipeline" / "final_merged.csv",
    ROOT / "tmp" / "wepoll_daily_append_2026-04-17" / "pipeline" / "final_merged.csv",
    ROOT / "tmp" / "wepoll_daily_append_2026-04-18" / "pipeline" / "final_merged.csv",
    ROOT / "tmp" / "wepoll_daily_append_2026-04-19" / "pipeline" / "final_merged.csv",
]


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def impact_value(row: dict[str, str]) -> float:
    fear = parse_float(row.get("fear_score"))
    greed = parse_float(row.get("greed_score"))
    engagement_weight = parse_float(row.get("engagement_weight"), 1.0)
    return engagement_weight * max(fear, greed)


def load_rows(paths: list[Path], start_date: str, end_date: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                date = (row.get("created_at") or "")[:10]
                if not (start_date <= date <= end_date):
                    continue
                key = (date, row.get("post_id", ""))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(dict(row))
    return rows


def build_histogram_rows(
    rows: list[dict[str, str]],
    *,
    bin_start: float,
    bin_end: float,
    bin_width: float,
) -> list[dict[str, str]]:
    num_bins = int(round((bin_end - bin_start) / bin_width))
    counts: Counter[int] = Counter()

    for row in rows:
        value = impact_value(row)
        if value < bin_start:
            index = 0
        elif value >= bin_end:
            index = num_bins - 1
        else:
            index = int((value - bin_start) // bin_width)
        counts[index] += 1

    out: list[dict[str, str]] = []
    total = len(rows) or 1
    for index in range(num_bins):
        left = bin_start + index * bin_width
        right = left + bin_width
        label = f"{left:.1f}-{right:.1f}"
        count = counts[index]
        out.append(
            {
                "impact_bin": label,
                "post_count": str(count),
                "share_pct": f"{100.0 * count / total:.2f}",
                "bin_start": f"{left:.1f}",
                "bin_end": f"{right:.1f}",
            }
        )
    return out


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", default="2026-04-13")
    parser.add_argument("--end-date", default="2026-04-19")
    parser.add_argument("--bin-start", type=float, default=0.0)
    parser.add_argument("--bin-end", type=float, default=14.0)
    parser.add_argument("--bin-width", type=float, default=0.5)
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        help="Optional final_merged.csv paths. When omitted, the current weekly defaults are used.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PANIC_PREPARED_DIR / "dw_post_impact_hist_latest_week.csv",
    )
    parser.add_argument("--dated-output", type=Path)
    args = parser.parse_args()

    inputs = args.input if args.input else DEFAULT_INPUTS
    rows = load_rows(inputs, args.start_date, args.end_date)
    if not rows:
        raise SystemExit("No matching rows found for the requested date range.")

    histogram_rows = build_histogram_rows(
        rows,
        bin_start=args.bin_start,
        bin_end=args.bin_end,
        bin_width=args.bin_width,
    )
    fieldnames = ["impact_bin", "post_count", "share_pct", "bin_start", "bin_end"]
    write_rows(args.output, histogram_rows, fieldnames)
    if args.dated_output:
        write_rows(args.dated_output, histogram_rows, fieldnames)

    print(args.output)
    if args.dated_output:
        print(args.dated_output)


if __name__ == "__main__":
    main()
