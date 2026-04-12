#!/usr/bin/env python3
"""Inspect Datawrapper themes or chart metadata."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


API_BASE = "https://api.datawrapper.de/v3"


def read_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def api_get(path: str) -> object:
    token = read_env("DATAWRAPPER_ACCESS_TOKEN")
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Datawrapper inspect error ({exc.code}) on GET {path}:\n{details}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("themes", help="List themes available to the account")

    chart = sub.add_parser("chart", help="Inspect a chart by id")
    chart.add_argument("chart_id")

    args = parser.parse_args()

    if args.command == "themes":
        payload = api_get("/themes")
    else:
        payload = api_get(f"/charts/{args.chart_id}")

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
