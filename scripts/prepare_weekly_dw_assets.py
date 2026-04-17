#!/usr/bin/env python3
"""Prepare Wepoll weekly Datawrapper CSV assets only."""

from __future__ import annotations

import csv
import os
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANIC_TIMESERIES_SOURCE = (
    ROOT.parent
    / "wepoll-panic"
    / "docs"
    / "report_assets"
    / "2026-04-06"
    / "psychology_participation_postcount_timeseries_append_2026-04-05.csv"
)
PANIC_BUBBLE_SOURCE = (
    ROOT.parent
    / "wepoll-panic"
    / "output"
    / "yearly_hybrid_batch_v4"
    / "weekly_bubble_points_2026-02-23_2026-04-05.csv"
)
RECENT_QUADRANT_SOURCE = Path(
    os.environ.get(
        "RECENT_QUADRANT_SOURCE",
        ROOT / "tmp" / "wepoll_daily_2026-04-13" / "quadrant.csv",
    )
)
PANIC_PREPARED_DIR = ROOT / "projects" / "wepoll-panic" / "prepared"
WEEKLY_REPORT_DATE = date.fromisoformat(
    os.environ.get("WEPOLL_WEEKLY_REPORT_DATE", str(date.today()))
)


def normalize_state_label(value: str) -> str:
    return "신중" if value == "경계" else value


def parse_date(value: str) -> datetime:
    return datetime.strptime(value[:10], "%Y-%m-%d")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def row_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    raise KeyError(f"Missing expected keys: {keys}")


def completed_week_end(report_date: date) -> date:
    if report_date.weekday() == 6:
        return report_date
    return report_date - timedelta(days=report_date.weekday() + 1)


def weekly_windows(report_date: date) -> dict[str, date]:
    week_end = completed_week_end(report_date)
    return {
        "report_date": report_date,
        "week_end": week_end,
        "week_start": week_end - timedelta(days=6),
        "timeseries_start": week_end - timedelta(days=41),
    }


def require_dates(source_name: str, rows_by_date: dict[str, dict[str, str]], start: date, end: date) -> None:
    missing = []
    current = start
    while current <= end:
        key = str(current)
        if key not in rows_by_date:
            missing.append(key)
        current += timedelta(days=1)
    if missing:
        raise SystemExit(
            f"{source_name} is missing required dates for weekly output: {', '.join(missing)}"
        )


def load_recent_rows() -> dict[str, dict[str, str]]:
    if not RECENT_QUADRANT_SOURCE.exists():
        return {}
    recent_rows = read_csv(RECENT_QUADRANT_SOURCE)
    out = {}
    for row in recent_rows:
        out[row["date"]] = {
            "date": row["date"],
            "state_label_ko": normalize_state_label(row["state_label_ko"]),
            "psychology_index_0_100": row_value(
                row,
                "psychology_index_0_100",
                "stance_index_0_100",
                "stance_fixed_0_100",
            ),
            "participation_index_0_100": row_value(
                row,
                "participation_index_0_100",
                "participation_fixed_0_100",
            ),
            "post_count": row["post_count"],
        }
    return out


def prepare_weekly_timeseries() -> tuple[Path, Path]:
    windows = weekly_windows(WEEKLY_REPORT_DATE)
    stitched = {row["date"]: dict(row) for row in read_csv(PANIC_TIMESERIES_SOURCE)}
    stitched.update(load_recent_rows())

    require_dates(
        "stitched weekly timeseries source",
        stitched,
        windows["timeseries_start"],
        windows["week_end"],
    )

    recent = [
        stitched[str(windows["timeseries_start"] + timedelta(days=offset))]
        for offset in range(42)
    ]

    out_rows: list[dict[str, object]] = []
    state_ranges: list[dict[str, str]] = []
    current_state = None
    current_start = None
    previous_date = None

    for idx, row in enumerate(recent, start=1):
        dt = parse_date(row["date"])
        out_rows.append(
            {
                "plot_seq": idx,
                "date": row["date"],
                "display_date": f"{dt.month}/{dt.day}",
                "state_label_ko": row["state_label_ko"],
                "psychology_index_0_100": f"{float(row['psychology_index_0_100']):.2f}",
                "participation_index_0_100": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": int(float(row["post_count"])),
            }
        )
        if row["state_label_ko"] != current_state:
            if current_state is not None:
                state_ranges.append(
                    {
                        "state_label_ko": current_state,
                        "start_date": current_start,
                        "end_date": previous_date,
                    }
                )
            current_state = row["state_label_ko"]
            current_start = row["date"]
        previous_date = row["date"]

    if current_state is not None:
        state_ranges.append(
            {
                "state_label_ko": current_state,
                "start_date": current_start,
                "end_date": previous_date,
            }
        )

    main_path = PANIC_PREPARED_DIR / "dw_weekly_timeseries_recent6w.csv"
    ranges_path = PANIC_PREPARED_DIR / "dw_weekly_timeseries_state_ranges_recent6w.csv"
    write_csv(
        main_path,
        out_rows,
        [
            "plot_seq",
            "date",
            "display_date",
            "state_label_ko",
            "psychology_index_0_100",
            "participation_index_0_100",
            "post_count",
        ],
    )
    write_csv(ranges_path, state_ranges, ["state_label_ko", "start_date", "end_date"])
    return main_path, ranges_path


def prepare_weekly_bubble() -> Path:
    windows = weekly_windows(WEEKLY_REPORT_DATE)
    recent_rows = load_recent_rows()
    if recent_rows:
        require_dates(
            "recent quadrant source",
            recent_rows,
            windows["week_start"],
            windows["week_end"],
        )
        week_rows = [
            {
                "date": row["date"],
                "week_range": f"{windows['week_start']}~{windows['week_end']}",
                "state_label_ko": row["state_label_ko"],
                "psychology_index_0_100": row["psychology_index_0_100"],
                "participation_index_0_100": row["participation_index_0_100"],
                "post_count": row["post_count"],
            }
            for row in (
                recent_rows[str(windows["week_start"] + timedelta(days=offset))]
                for offset in range(7)
            )
        ]
    else:
        week_key = f"{windows['week_start']}~{windows['week_end']}"
        week_rows = [row for row in read_csv(PANIC_BUBBLE_SOURCE) if row["week_range"] == week_key]
        week_rows.sort(key=lambda row: row["date"])
        if len(week_rows) != 7:
            raise SystemExit(
                "bubble baseline source is missing the required completed week "
                f"{week_key}"
            )

    out_rows: list[dict[str, object]] = []
    for idx, row in enumerate(week_rows, start=1):
        out_rows.append(
            {
                "day_seq": idx,
                "day_label": f"{idx}일차",
                "date": row["date"],
                "week_range": row["week_range"],
                "state_label_ko": normalize_state_label(row["state_label_ko"]),
                "심리(Bear-Bull) 지수": f"{float(row['psychology_index_0_100']):.2f}",
                "참여 지수": f"{float(row['participation_index_0_100']):.2f}",
                "post_count": int(float(row["post_count"])),
            }
        )

    path = PANIC_PREPARED_DIR / "dw_weekly_bubble_latest_week.csv"
    write_csv(
        path,
        out_rows,
        [
            "day_seq",
            "day_label",
            "date",
            "week_range",
            "state_label_ko",
            "심리(Bear-Bull) 지수",
            "참여 지수",
            "post_count",
        ],
    )
    return path


def main() -> None:
    timeseries_path, ranges_path = prepare_weekly_timeseries()
    bubble_path = prepare_weekly_bubble()
    print(f"timeseries={timeseries_path}")
    print(f"ranges={ranges_path}")
    print(f"bubble={bubble_path}")


if __name__ == "__main__":
    main()
