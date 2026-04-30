#!/usr/bin/env python3
"""Prepare Autopark Datawrapper input placeholders and chart plans."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "market_charts.json"
PREPARED_DIR = PROJECT_ROOT / "prepared"
CHARTS_DIR = PROJECT_ROOT / "charts"


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_charts(config: dict) -> list[dict]:
    charts: list[dict] = []
    for group in config.get("groups", []):
        for chart in group.get("charts", []):
            charts.append({**chart, "group_id": group["id"], "group_title": group["title"]})
    return charts


def find_chart(config: dict, chart_id: str) -> dict:
    for chart in iter_charts(config):
        if chart["id"] == chart_id:
            return chart
    raise SystemExit(f"Unknown chart id: {chart_id}")


def write_placeholder_csv(chart: dict, target_date: str) -> Path:
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = PREPARED_DIR / f"{chart['id']}-{target_date}.csv"
    symbols = chart.get("symbols") or [{"label": "TICKER", "symbol": "TICKER"}]
    labels = [symbol["label"] for symbol in symbols]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", *labels])
        writer.writeheader()
        writer.writerow({"date": target_date, **{label: "" for label in labels}})
    return csv_path


def write_chart_spec(chart: dict, csv_path: Path, target_date: str, theme: str) -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    spec_path = CHARTS_DIR / f"{chart['id']}-datawrapper.json"
    subtitle = f"기준일: {target_date}" if chart.get("show_subtitle", True) else ""
    describe_intro = f"{chart['group_title']} / {chart.get('target_window', '')}".strip()
    if not chart.get("show_subtitle", True):
        describe_intro = ""
    spec = {
        "project": "autopark",
        "slug": chart["id"],
        "title": chart["title"],
        "subtitle": subtitle,
        "chart_type": chart["chart_type"],
        "theme": theme,
        "prepared_csv": f"../prepared/{csv_path.name}",
        "source_name": ", ".join(chart.get("candidate_sources", [])[:2]),
        "byline": "",
        "metadata": {
            "describe": {
                "intro": describe_intro,
                "aria-description": f"Autopark chart placeholder for {chart['title']}"
            },
            "publish": {
                "embed-width": 600
            }
        }
    }
    if chart.get("show_series_labels") is False and chart["chart_type"] in {"d3-lines", "multiple-lines"}:
        spec["metadata"].setdefault("visualize", {})["labeling"] = "off"
    elif chart.get("labeling") and chart["chart_type"] in {"d3-lines", "multiple-lines"}:
        spec["metadata"].setdefault("visualize", {})["labeling"] = chart["labeling"]
    if spec_path.exists():
        existing = json.loads(spec_path.read_text(encoding="utf-8"))
        if existing.get("chart_id"):
            spec["chart_id"] = existing["chart_id"]
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return spec_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--chart", help="Prepare one chart id")
    parser.add_argument("--list", action="store_true", help="List configured chart plans")
    parser.add_argument("--write-placeholders", action="store_true", help="Write placeholder CSV/spec files")
    args = parser.parse_args()

    config = load_config(args.config)
    charts = [find_chart(config, args.chart)] if args.chart else iter_charts(config)

    if args.list:
        print(json.dumps({"ok": True, "charts": charts}, ensure_ascii=False, indent=2))
        return

    if not args.write_placeholders:
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "plan",
                    "date": args.date,
                    "charts": [
                        {
                            "id": chart["id"],
                            "title": chart["title"],
                            "preferred_data_source": chart.get("preferred_data_source"),
                            "status": chart.get("status"),
                        }
                        for chart in charts
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    written = []
    theme = config.get("default_theme", "datawrapper-high-contrast")
    for chart in charts:
        csv_path = write_placeholder_csv(chart, args.date)
        spec_path = write_chart_spec(chart, csv_path, args.date, theme)
        written.append({"chart": chart["id"], "prepared_csv": str(csv_path), "spec": str(spec_path)})
    print(json.dumps({"ok": True, "date": args.date, "written": written}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
