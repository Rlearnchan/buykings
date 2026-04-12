#!/usr/bin/env python3
"""Export a Datawrapper chart as PNG."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://api.datawrapper.de/v3"


def read_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def request_bytes(path: str) -> bytes:
    token = read_env("DATAWRAPPER_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    request = urllib.request.Request(f"{API_BASE}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Datawrapper export error ({exc.code}) on GET {path}:\n{details}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart_id", help="Datawrapper chart id")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    output_path = pathlib.Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    query = urllib.parse.urlencode({"width": args.width, "scale": args.scale})
    payload = request_bytes(f"/charts/{args.chart_id}/export/png?{query}")
    output_path.write_bytes(payload)

    print(
        json.dumps(
            {
                "ok": True,
                "chart_id": args.chart_id,
                "output": str(output_path),
                "width": args.width,
                "scale": args.scale,
                "bytes": output_path.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
