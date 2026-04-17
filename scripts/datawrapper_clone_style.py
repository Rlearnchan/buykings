#!/usr/bin/env python3
"""Clone live Datawrapper styling metadata from one chart to another."""

from __future__ import annotations

import argparse
import copy
import json

from datawrapper_publish import DatawrapperClient
from datawrapper_publish import read_env


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
    parser.add_argument("target_chart_id")
    parser.add_argument("--title")
    parser.add_argument("--note")
    parser.add_argument("--source-name")
    parser.add_argument("--line-start-date")
    parser.add_argument("--line-end-date")
    parser.add_argument("--highlight-start-date")
    parser.add_argument("--highlight-end-date")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    client = DatawrapperClient(read_env("DATAWRAPPER_ACCESS_TOKEN"))
    source = client.get_chart(args.source_chart_id)

    metadata = copy.deepcopy(source.get("metadata", {}))
    sanitize_publish(metadata)

    if args.note:
        metadata.setdefault("annotate", {})
        metadata["annotate"]["notes"] = args.note

    if args.source_name:
        metadata.setdefault("describe", {})
        metadata["describe"]["source-name"] = args.source_name

    if all([args.line_start_date, args.line_end_date, args.highlight_start_date, args.highlight_end_date]):
        update_line_annotations(
            metadata,
            args.line_start_date,
            args.line_end_date,
            args.highlight_start_date,
            args.highlight_end_date,
        )

    payload = {
        "title": args.title or source.get("title"),
        "metadata": metadata,
    }
    patched = client.patch_metadata(args.target_chart_id, payload)
    result = {"patched": patched}
    if args.publish:
        result["published"] = client.publish_chart(args.target_chart_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
