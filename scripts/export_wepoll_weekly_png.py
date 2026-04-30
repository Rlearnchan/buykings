#!/usr/bin/env python3
"""Export a Wepoll weekly chart PNG with the current shared layout defaults."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_SCRIPT = ROOT / "scripts" / "datawrapper_export_png.py"
LOGO_SCRIPT = ROOT / "scripts" / "datawrapper_brand_logo.py"

PROFILES = {
    "timeseries": {
        "width": 600,
        "scale": 2,
        "logo_height_ratio": 0.10,
        "margin_top_px": 15,
        "margin_right_px": 30,
    },
    "bubble": {
        "width": 600,
        "scale": 2,
        "logo_height_ratio": 0.08,
        "margin_top_px": 15,
        "margin_right_px": 30,
    },
    "impact-hist": {
        "width": 600,
        "scale": 2,
        "logo_height_ratio": 0.09,
        "margin_top_px": 15,
        "margin_right_px": 30,
    },
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(PROFILES), help="Weekly chart kind")
    parser.add_argument("chart_id", help="Datawrapper chart id")
    parser.add_argument("output", help="Output PNG path")
    args = parser.parse_args()

    profile = PROFILES[args.kind]
    output = str(Path(args.output).resolve())

    run(
        [
            sys.executable,
            str(EXPORT_SCRIPT),
            args.chart_id,
            output,
            "--width",
            str(profile["width"]),
            "--scale",
            str(profile["scale"]),
        ]
    )
    run(
        [
            sys.executable,
            str(LOGO_SCRIPT),
            output,
            "--logo-height-ratio",
            str(profile["logo_height_ratio"]),
            "--margin-top-px",
            str(profile["margin_top_px"]),
            "--margin-right-px",
            str(profile["margin_right_px"]),
        ]
    )


if __name__ == "__main__":
    main()
