#!/usr/bin/env python3
"""Create a new Datawrapper chart using another chart's live styling metadata."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib

from datawrapper_publish import DatawrapperClient
from datawrapper_publish import build_create_payload
from datawrapper_publish import read_env
from datawrapper_publish import resolve_spec_path


def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sanitize_publish(metadata: dict) -> None:
    publish = metadata.get("publish")
    if not isinstance(publish, dict):
        return
    publish.pop("embed-codes", None)
    publish.pop("export-pdf", None)
    publish.pop("chart-height", None)


def update_line_annotations(metadata: dict, start_date: str, end_date: str, highlight_start: str, highlight_end: str) -> None:
    visualize = metadata.get("visualize", {})
    annotations = visualize.get("range-annotations", [])
    for item in annotations:
        position = item.get("position", {})
        if item.get("type") == "y":
            position["x0"] = f"{start_date} 00:00"
            position["x1"] = f"{end_date} 00:00"
        if item.get("type") == "x" and item.get("display") == "range":
            position["x0"] = f"{highlight_start} 00:00"
            position["x1"] = f"{highlight_end} 00:00"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_chart_id")
    parser.add_argument("spec")
    parser.add_argument("--note")
    parser.add_argument("--line-start-date")
    parser.add_argument("--line-end-date")
    parser.add_argument("--highlight-start-date")
    parser.add_argument("--highlight-end-date")
    args = parser.parse_args()

    spec_path = pathlib.Path(args.spec).resolve()
    spec = load_json(spec_path)
    csv_path = resolve_spec_path(spec_path, spec["prepared_csv"])
    if not csv_path.exists():
        raise SystemExit(f"Prepared CSV not found: {csv_path}")

    client = DatawrapperClient(read_env("DATAWRAPPER_ACCESS_TOKEN"))
    source = client.get_chart(args.source_chart_id)
    metadata = copy.deepcopy(source.get("metadata", {}))
    sanitize_publish(metadata)

    metadata.setdefault("describe", {})
    metadata["describe"]["source-name"] = spec.get("source_name", metadata["describe"].get("source-name", ""))

    if args.note:
        metadata.setdefault("annotate", {})
        metadata["annotate"]["notes"] = args.note

    if all([args.line_start_date, args.line_end_date, args.highlight_start_date, args.highlight_end_date]):
        update_line_annotations(
            metadata,
            args.line_start_date,
            args.line_end_date,
            args.highlight_start_date,
            args.highlight_end_date,
        )

    create_payload = build_create_payload(spec)
    created = client.create_chart(create_payload)
    chart_id = created["id"]
    client.upload_csv(chart_id, csv_path.read_bytes())
    client.patch_metadata(
        chart_id,
        {
            "title": spec["title"],
            "metadata": metadata,
        },
    )
    published = client.publish_chart(chart_id)
    result = {
        "chart_id": chart_id,
        "title": spec["title"],
        "prepared_csv": str(csv_path),
        "public_url": f"https://datawrapper.dwcdn.net/{chart_id}/{published.get('publicVersion')}/",
        "edit_url": f"https://app.datawrapper.de/chart/{chart_id}/edit",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
