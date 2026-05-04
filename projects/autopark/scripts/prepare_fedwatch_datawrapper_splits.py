#!/usr/bin/env python3
"""Split the FedWatch probability table into short/long Datawrapper specs."""

from __future__ import annotations

import argparse
import csv
import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHARTS_DIR = PROJECT_ROOT / "charts"
PREPARED_DIR = PROJECT_ROOT / "prepared"
BASE_SPEC = CHARTS_DIR / "fedwatch-conditional-probabilities-datawrapper.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def default_base_spec(target_date: str) -> dict:
    subtitle = f"{datetime.fromisoformat(target_date).strftime('%y.%m.%d')} 기준"
    numeric_columns = {
        column: {
            "align": "center",
            "width": 0.1,
            "format": "0.0",
            "heatmap": {"enabled": True},
            "append": "%",
        }
        for column in [
            "200-225",
            "225-250",
            "250-275",
            "275-300",
            "300-325",
            "325-350",
            "350-375",
            "375-400",
            "400-425",
            "425-450",
        ]
    }
    return {
        "project": "autopark",
        "slug": "fedwatch-conditional-probabilities",
        "title": "FedWatch 조건부 금리확률",
        "subtitle": subtitle,
        "chart_type": "tables",
        "theme": "datawrapper-high-contrast",
        "prepared_csv": "",
        "source_name": "CME FedWatch",
        "source_url": "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html",
        "byline": "",
        "metadata": {
            "describe": {
                "intro": subtitle,
                "aria-description": "CME FedWatch 조건부 목표금리 확률 히트맵",
            },
            "publish": {
                "embed-width": 760,
                "embed-height": 520,
            },
            "visualize": {
                "perPage": 20,
                "striped": False,
                "pagination": False,
                "searchable": False,
                "showHeader": True,
                "columns": {
                    "회의일": {"align": "left", "width": 0.14},
                    **numeric_columns,
                },
                "heatmap": {
                    "palette": 0,
                    "mode": "continuous",
                    "stops": "equidistant",
                    "colors": [
                        {"color": "#ffffff", "position": 0},
                        {"color": "#ffe8cf", "position": 0.5},
                        {"color": "#e85d3f", "position": 1},
                    ],
                    "rangeMax": "100",
                    "rangeMin": "0",
                    "stopCount": 3,
                    "hideValues": False,
                    "showLegend": False,
                },
                "legend": {
                    "enabled": False,
                },
            },
        },
    }


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise SystemExit(f"Empty FedWatch CSV: {path}")
    return rows[0], rows[1:]


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def display_dt(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("Asia/Seoul")).strftime("%y.%m.%d %H:%M KST")
    except ValueError:
        return value[:16]


def fedwatch_subtitle(target_date: str, base: dict) -> str:
    payload = load_json(RAW_DIR / target_date / "cme-fedwatch.json")
    captured = display_dt(payload.get("captured_at") or payload.get("created_at") or payload.get("updated_at"))
    basis = f"CME FedWatch 화면 {captured} 기준" if captured else f"CME FedWatch 화면 {datetime.fromisoformat(target_date).strftime('%y.%m.%d')} 기준"
    base_subtitle = clean(base.get("subtitle"))
    suffix = ""
    if "현재 기준금리" in base_subtitle:
        rate = base_subtitle.split("현재 기준금리", 1)[-1]
        rate = rate.replace("·", " ").strip()
        suffix = f" · 현재 기준금리 {rate}" if rate else " · 현재 기준금리"
    return basis + suffix


def short_date(value: str) -> str:
    match = re.match(r"^(20\d{2})-(\d{2})-(\d{2})$", value)
    if not match:
        return value
    year, month, day = match.groups()
    return f"{year[2:]}.{month}.{day}@@{year}{month}{day}"


def strip_percent(value: str) -> str:
    text = clean(value).replace("%", "")
    return text or "0.0"


def read_raw_fedwatch(target_date: str) -> tuple[list[str], list[list[str]]]:
    path = RAW_DIR / target_date / "cme-fedwatch.json"
    payload = load_json(path)
    fedwatch = ((payload.get("extracted") or {}).get("fedwatch") or {})
    table = fedwatch.get("selected_table") or {}
    raw_rows = table.get("rows") or fedwatch.get("fallback_rows") or []
    parsed: list[list[str]] = []
    for row in raw_rows:
        cells = row if isinstance(row, list) else [str(row)]
        if len(cells) == 1:
            cells = re.split(r"\s+", cells[0].strip())
        cells = [clean(cell) for cell in cells if clean(cell)]
        if cells:
            parsed.append(cells)
    header_index = next((index for index, row in enumerate(parsed) if "meeting date" in " ".join(row).lower()), None)
    if header_index is None:
        raise SystemExit(f"FedWatch raw table header not found: {path}")
    raw_headers = parsed[header_index]
    headers = ["회의일" if cell.lower() == "meeting date" else cell for cell in raw_headers]
    rows = []
    for row in parsed[header_index + 1 :]:
        if len(row) < 3 or not re.match(r"^20\d{2}-\d{2}-\d{2}$", row[0]):
            continue
        normalized = [short_date(row[0]), *[strip_percent(cell) for cell in row[1 : len(headers)]]]
        rows.append(normalized)
    if not rows:
        raise SystemExit(f"FedWatch raw table rows not found: {path}")
    return headers, rows


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def split_rows(rows: list[list[str]]) -> tuple[list[list[str]], list[list[str]]]:
    midpoint = (len(rows) + 1) // 2
    return rows[:midpoint], rows[midpoint:]


def spec_for(base: dict, *, slug: str, title: str, subtitle: str, prepared_name: str, row_count: int) -> dict:
    spec = deepcopy(base)
    spec["slug"] = slug
    spec["title"] = title
    spec["subtitle"] = subtitle
    spec["prepared_csv"] = f"../prepared/{prepared_name}"
    spec.pop("chart_id", None)

    metadata = spec.setdefault("metadata", {})
    describe = metadata.setdefault("describe", {})
    describe["intro"] = subtitle
    describe["aria-description"] = f"{title} 히트맵"

    publish = metadata.setdefault("publish", {})
    publish["embed-width"] = 760
    publish["embed-height"] = max(300, min(520, 190 + row_count * 54))

    visualize = metadata.setdefault("visualize", {})
    visualize["perPage"] = max(1, row_count)
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--base-spec", type=Path, default=BASE_SPEC)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()

    input_path = args.input or (PREPARED_DIR / f"fedwatch-conditional-probabilities-{args.date}.csv")
    if input_path.exists():
        headers, rows = read_csv(input_path)
    else:
        headers, rows = read_raw_fedwatch(args.date)
        write_csv(input_path, headers, rows)
    short_rows, long_rows = split_rows(rows)
    base = load_json(args.base_spec) if args.base_spec.exists() else default_base_spec(args.date)
    subtitle = fedwatch_subtitle(args.date, base)

    outputs = []
    for suffix, title, selected_rows in [
        ("short-term", "FedWatch 단기 금리확률", short_rows),
        ("long-term", "FedWatch 장기 금리확률", long_rows),
    ]:
        prepared_name = f"fedwatch-conditional-probabilities-{suffix}-{args.date}.csv"
        spec_name = f"fedwatch-conditional-probabilities-{suffix}-datawrapper.json"
        write_csv(PREPARED_DIR / prepared_name, headers, selected_rows)
        spec = spec_for(
            base,
            slug=f"fedwatch-conditional-probabilities-{suffix}",
            title=title,
            subtitle=subtitle,
            prepared_name=prepared_name,
            row_count=len(selected_rows),
        )
        spec_path = CHARTS_DIR / spec_name
        if spec_path.exists():
            existing_spec = load_json(spec_path)
            if existing_spec.get("chart_id"):
                spec["chart_id"] = existing_spec["chart_id"]
        write_json(spec_path, spec)
        outputs.append(
            {
                "part": suffix,
                "title": title,
                "rows": len(selected_rows),
                "prepared_csv": str(PREPARED_DIR / prepared_name),
                "spec": str(spec_path),
            }
        )

    print(json.dumps({"ok": True, "date": args.date, "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
