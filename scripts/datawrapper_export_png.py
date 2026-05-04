#!/usr/bin/env python3
"""Export a Datawrapper chart as PNG."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://api.datawrapper.de/v3"
ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LOGO = ROOT / "logo" / "buykings research cropped.jpg"


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip().lstrip("\ufeff"), value.strip().strip('"').strip("'"))


def read_env(name: str) -> str:
    load_local_env()
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


def request_json(path: str) -> dict:
    return json.loads(request_bytes(path).decode("utf-8"))


def resolve_export_width(chart_id: str, explicit_width: int | None) -> int:
    if explicit_width:
        return explicit_width
    chart = request_json(f"/charts/{chart_id}")
    publish = chart.get("metadata", {}).get("publish", {})
    embed_width = publish.get("embed-width")
    if isinstance(embed_width, int) and embed_width > 0:
        return embed_width
    return 600


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chart_id", help="Datawrapper chart id")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--width", type=int, help="Override export width; defaults to the chart's publish embed-width")
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--brand-logo", action="store_true", help="Overlay the BuyKings Research logo after export")
    parser.add_argument("--logo-path", default=str(DEFAULT_LOGO), help="Logo asset path used with --brand-logo")
    parser.add_argument("--logo-height-ratio", type=float, default=0.10)
    parser.add_argument("--logo-max-height-px", type=int, default=96)
    parser.add_argument("--logo-margin-top-ratio", type=float, default=0.03)
    parser.add_argument("--logo-margin-right-ratio", type=float, default=0.025)
    parser.add_argument("--logo-opacity", type=float, default=1.0)
    args = parser.parse_args()

    output_path = pathlib.Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_width = resolve_export_width(args.chart_id, args.width)
    query = urllib.parse.urlencode({"width": export_width, "scale": args.scale})
    payload = request_bytes(f"/charts/{args.chart_id}/export/png?{query}")
    output_path.write_bytes(payload)

    if args.brand_logo:
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "datawrapper_brand_logo.py"),
                str(output_path),
                "--logo",
                str(pathlib.Path(args.logo_path).resolve()),
                "--logo-height-ratio",
                str(args.logo_height_ratio),
                "--logo-max-height-px",
                str(args.logo_max_height_px),
                "--margin-top-ratio",
                str(args.logo_margin_top_ratio),
                "--margin-right-ratio",
                str(args.logo_margin_right_ratio),
                "--opacity",
                str(args.logo_opacity),
            ],
            check=True,
        )

    print(
        json.dumps(
            {
                "ok": True,
                "chart_id": args.chart_id,
                "output": str(output_path),
                "width": export_width,
                "scale": args.scale,
                "bytes": output_path.stat().st_size,
                "brand_logo": args.brand_logo,
                "logo_max_height_px": args.logo_max_height_px if args.brand_logo else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
