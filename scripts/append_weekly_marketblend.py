#!/usr/bin/env python3
"""Append new weekly daily points using the existing market-blend baseline without changing old values."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import mean
from statistics import pstdev


FEATURE_SPECS = [
    ("dominant_diff", 1.0),
    ("high_share_diff", 1.0),
    ("greed_weighted_mean", 1.0),
    ("fear_weighted_mean", -1.0),
]


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def parse_number(value: str) -> float | None:
    value = (value or "").strip().replace(",", "")
    if not value:
        return None
    mult = 1.0
    if value.endswith("B"):
        mult = 1_000_000_000
        value = value[:-1]
    elif value.endswith("M"):
        mult = 1_000_000
        value = value[:-1]
    elif value.endswith("%"):
        value = value[:-1]
    try:
        return float(value) * mult
    except Exception:
        return None


def normalize_date(value: str) -> str:
    value = value.strip().replace('"', "").replace(" ", "")
    y, m, d = value.split("-")
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dedupe_rows_by_date(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_date: dict[str, dict[str, str]] = {}
    for row in rows:
        by_date[row["date"]] = dict(row)
    return [by_date[day] for day in sorted(by_date)]


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_params(rows: list[dict[str, str]], baseline_start: str, baseline_end: str) -> list[dict[str, float | str]]:
    baseline = [r for r in rows if baseline_start <= r["date"] <= baseline_end]
    bulls = [r for r in rows if r.get("anchor_label") == "bull"]
    bears = [r for r in rows if r.get("anchor_label") == "bear"]
    params: list[dict[str, float | str]] = []
    for feature, sign in FEATURE_SPECS:
        base_values = [parse_float(r[feature]) for r in baseline]
        base_mean = mean(base_values)
        base_std = pstdev(base_values) or 1.0
        bull_mean = mean(parse_float(r[feature]) for r in bulls)
        bear_mean = mean(parse_float(r[feature]) for r in bears)
        separation = max((bull_mean - bear_mean) * sign, 0.0001)
        params.append(
            {
                "feature": feature,
                "sign": sign,
                "baseline_mean": base_mean,
                "baseline_std": base_std,
                "anchor_separation": separation,
            }
        )
    return params


def raw_score(row: dict[str, str], params: list[dict[str, float | str]]) -> float:
    score = 0.0
    for p in params:
        feature = str(p["feature"])
        sign = float(p["sign"])
        base_mean = float(p["baseline_mean"])
        base_std = float(p["baseline_std"])
        weight = float(p["anchor_separation"])
        z = (parse_float(row[feature]) - base_mean) / base_std
        score += sign * weight * z
    return score


def apply_reliability(anchored: float, post_count: float, active_share: float) -> tuple[float, float]:
    post_reliability = min(1.0, math.sqrt(max(post_count, 0.0) / 80.0))
    emotion_reliability = min(1.0, active_share / 0.22)
    reliability = max(0.15, min(1.0, 0.65 * post_reliability + 0.35 * emotion_reliability))
    shrunken = 50.0 + (anchored - 50.0) * reliability
    return reliability, max(0.0, min(100.0, shrunken))


def zscore(v: float, mean_value: float, std_value: float) -> float:
    if math.isclose(std_value, 0.0):
        return 0.0
    return (v - mean_value) / std_value


def remap_threshold_to_50(value: float, midpoint: float) -> float:
    if midpoint <= 0:
        midpoint = 1.0
    if midpoint >= 100:
        midpoint = 99.0
    if value <= midpoint:
        return max(0.0, min(50.0, 50.0 * (value / midpoint)))
    return max(50.0, min(100.0, 50.0 + 50.0 * ((value - midpoint) / (100.0 - midpoint))))


def classify_label(stance_idx: float, participation_idx: float) -> str:
    if participation_idx >= 50:
        return "탐욕" if stance_idx >= 50 else "공포"
    if stance_idx < 45:
        return "신중"
    return "낙관"


def load_series(path: Path, prefix: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = normalize_date(row["날짜"])
            close = parse_number(row["종가"])
            open_ = parse_number(row["시가"])
            high = parse_number(row["고가"])
            low = parse_number(row["저가"])
            volume = parse_number(row.get("거래량", ""))
            change_pct = parse_number(row.get("변동 %", ""))
            rows.append(
                {
                    "date": date,
                    f"{prefix}_close": "" if close is None else f"{close:.6f}",
                    f"{prefix}_open": "" if open_ is None else f"{open_:.6f}",
                    f"{prefix}_high": "" if high is None else f"{high:.6f}",
                    f"{prefix}_low": "" if low is None else f"{low:.6f}",
                    f"{prefix}_volume": "" if volume is None else f"{volume:.0f}",
                    f"{prefix}_change_pct": "" if change_pct is None else f"{change_pct:.6f}",
                }
            )
    return rows


def build_market_map(kospi: Path, kosdaq: Path, vkospi: Path) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for path, prefix in [(kospi, "kospi"), (kosdaq, "kosdaq"), (vkospi, "vkospi")]:
        for row in load_series(path, prefix):
            merged.setdefault(row["date"], {"date": row["date"]}).update(row)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-stance", required=True, type=Path)
    parser.add_argument("--new-features", required=True, type=Path)
    parser.add_argument("--timeseries-old", required=True, type=Path)
    parser.add_argument("--market-kospi", required=True, type=Path)
    parser.add_argument("--market-kosdaq", required=True, type=Path)
    parser.add_argument("--market-vkospi", required=True, type=Path)
    parser.add_argument("--market-existing", type=Path)
    parser.add_argument("--end-date", default="2026-04-12")
    parser.add_argument("--baseline-start", default="2025-04-01")
    parser.add_argument("--baseline-end", default="2025-12-31")
    parser.add_argument("--participation-mid", type=float, default=52.0)
    parser.add_argument("--stance-mid", type=float, default=60.0)
    parser.add_argument("--low-participation-positive-mid", type=float, default=56.0)
    parser.add_argument("--output-stance", required=True, type=Path)
    parser.add_argument("--output-quadrant", required=True, type=Path)
    parser.add_argument("--output-timeseries", required=True, type=Path)
    parser.add_argument("--output-bubble", required=True, type=Path)
    parser.add_argument("--output-ranges", type=Path)
    args = parser.parse_args()

    old_rows = dedupe_rows_by_date(load_rows(args.old_stance))
    timeseries_old_rows = dedupe_rows_by_date(load_rows(args.timeseries_old))
    last_published_date = timeseries_old_rows[-1]["date"]
    old_rows = [r for r in old_rows if r["date"] <= last_published_date]
    new_feature_rows = [r for r in load_rows(args.new_features) if last_published_date < r["date"] <= args.end_date]

    params = build_params(old_rows, args.baseline_start, args.baseline_end)
    bulls = [parse_float(r["stance_calibrated_raw"]) for r in old_rows if r.get("anchor_label") == "bull"]
    bears = [parse_float(r["stance_calibrated_raw"]) for r in old_rows if r.get("anchor_label") == "bear"]
    midpoint = (mean(bulls) + mean(bears)) / 2
    radius = max(abs(parse_float(r["stance_calibrated_raw"]) - midpoint) for r in old_rows) or 1.0

    appended_rows = [dict(r) for r in old_rows]
    for row in new_feature_rows:
        enriched = dict(row)
        raw = raw_score(row, params)
        anchored = max(0.0, min(100.0, 50.0 + 50.0 * (raw - midpoint) / radius))
        reliability, shrunken = apply_reliability(
            anchored,
            parse_float(row.get("post_count", 0)),
            parse_float(row.get("active_emotion_share", 0)),
        )
        enriched["stance_calibrated_raw"] = f"{raw:.6f}"
        enriched["stance_calibrated_0_100"] = f"{anchored:.6f}"
        enriched["stance_reliability"] = f"{reliability:.6f}"
        enriched["stance_calibrated_shrunk_0_100"] = f"{shrunken:.6f}"
        appended_rows.append(enriched)
    appended_rows.sort(key=lambda r: r["date"])
    write_rows(args.output_stance, appended_rows, list(appended_rows[0].keys()))

    market_map = {}
    if args.market_existing and args.market_existing.exists():
        market_map = {row["date"]: row for row in load_rows(args.market_existing)}
    market_map.update(build_market_map(args.market_kospi, args.market_kosdaq, args.market_vkospi))
    feature_map = {r["date"]: r for r in appended_rows}
    dates = [r["date"] for r in appended_rows]

    emotion_baseline = [parse_float(feature_map[d]["active_emotion_share"]) for d in dates if args.baseline_start <= d <= args.baseline_end]
    emotion_mean = mean(emotion_baseline)
    emotion_std = pstdev(emotion_baseline) or 1.0

    post_baseline = [math.log1p(parse_float(feature_map[d]["post_count"])) for d in dates if args.baseline_start <= d <= args.baseline_end]
    post_mean = mean(post_baseline)
    post_std = pstdev(post_baseline) or 1.0

    turnover_raw = []
    for d in dates:
        m = market_map.get(d)
        if not m:
            turnover_raw.append(None)
            continue
        total = parse_float(m.get("kospi_volume", "")) + parse_float(m.get("kosdaq_volume", ""))
        turnover_raw.append(math.log1p(total) if total > 0 else None)
    turnover_baseline = [v for d, v in zip(dates, turnover_raw) if v is not None and args.baseline_start <= d <= args.baseline_end]
    turn_mean = mean(turnover_baseline)
    turn_std = pstdev(turnover_baseline) or 1.0

    quadrant_rows: list[dict[str, str]] = []
    prev_stance = None
    prev_part = None
    prev_label = None
    for d, turnover in zip(dates, turnover_raw):
        row = feature_map[d]
        e_fix = max(0.0, min(100.0, 50.0 + 15.0 * zscore(parse_float(row["active_emotion_share"]), emotion_mean, emotion_std)))
        p_fix = max(0.0, min(100.0, 50.0 + 10.0 * zscore(math.log1p(parse_float(row["post_count"])), post_mean, post_std)))
        if turnover is None:
            t_fix = 50.0
        else:
            t_fix = max(0.0, min(100.0, 50.0 + 10.0 * zscore(turnover, turn_mean, turn_std)))
        participation_internal = max(0.0, min(100.0, 0.45 * e_fix + 0.15 * p_fix + 0.40 * t_fix))

        stance_internal = parse_float(row["stance_calibrated_shrunk_0_100"])
        participation_idx = remap_threshold_to_50(participation_internal, args.participation_mid)
        stance_mid = args.stance_mid if participation_internal >= args.participation_mid else args.low_participation_positive_mid
        stance_idx = remap_threshold_to_50(stance_internal, stance_mid)
        label = classify_label(stance_idx, participation_idx)

        dx = 0.0 if prev_stance is None else stance_idx - prev_stance
        dy = 0.0 if prev_part is None else participation_idx - prev_part
        quadrant_rows.append(
            {
                "date": d,
                "stance_internal_0_100": f"{stance_internal:.6f}",
                "participation_internal_0_100": f"{participation_internal:.6f}",
                "stance_index_0_100": f"{stance_idx:.6f}",
                "participation_index_0_100": f"{participation_idx:.6f}",
                "state_label_ko": label,
                "stance_delta": f"{dx:.6f}",
                "participation_delta": f"{dy:.6f}",
                "prev_state_label_ko": prev_label or "",
                "anchor_label": row.get("anchor_label", ""),
                "post_count": row.get("post_count", ""),
            }
        )
        prev_stance = stance_idx
        prev_part = participation_idx
        prev_label = label
    write_rows(args.output_quadrant, quadrant_rows, list(quadrant_rows[0].keys()))

    appended_map = {r["date"]: r for r in quadrant_rows if "2026-04-06" <= r["date"] <= args.end_date}
    replacement_start = min(appended_map) if appended_map else None
    combined = []
    for row in timeseries_old_rows:
        if replacement_start and row["date"] >= replacement_start:
            continue
        combined.append(dict(row))
    for date_key in sorted(appended_map):
        combined.append(
            {
                "date": date_key,
                "state_label_ko": appended_map[date_key]["state_label_ko"],
                "psychology_index_0_100": f"{parse_float(appended_map[date_key]['stance_index_0_100']):.6f}",
                "participation_index_0_100": f"{parse_float(appended_map[date_key]['participation_index_0_100']):.6f}",
                "post_count": appended_map[date_key]["post_count"],
            }
        )
    write_rows(args.output_timeseries, combined, ["date", "state_label_ko", "psychology_index_0_100", "participation_index_0_100", "post_count"])

    if args.output_ranges:
        ranges = []
        current_state = None
        current_start = None
        previous_date = None
        for row in combined:
            if row["state_label_ko"] != current_state:
                if current_state is not None:
                    ranges.append({"state_label_ko": current_state, "start_date": current_start, "end_date": previous_date})
                current_state = row["state_label_ko"]
                current_start = row["date"]
            previous_date = row["date"]
        if current_state is not None:
            ranges.append({"state_label_ko": current_state, "start_date": current_start, "end_date": previous_date})
        write_rows(args.output_ranges, ranges, ["state_label_ko", "start_date", "end_date"])

    bubble_rows = []
    for idx, date_key in enumerate(sorted(appended_map), start=1):
        row = appended_map[date_key]
        bubble_rows.append(
            {
                "day_seq": str(idx),
                "day_label": f"{idx}일차",
                "date": date_key,
                "week_range": f"2026-04-06~{args.end_date}",
                "state_label_ko": row["state_label_ko"],
                "심리(Bear-Bull) 지수": f"{parse_float(row['stance_index_0_100']):.6f}",
                "참여 지수": f"{parse_float(row['participation_index_0_100']):.6f}",
                "post_count": row["post_count"],
            }
        )
    write_rows(args.output_bubble, bubble_rows, ["day_seq", "day_label", "date", "week_range", "state_label_ko", "심리(Bear-Bull) 지수", "참여 지수", "post_count"])

    print(args.output_timeseries)
    print(args.output_bubble)


if __name__ == "__main__":
    main()
