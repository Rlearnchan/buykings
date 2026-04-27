#!/usr/bin/env python3
"""Overlay the BuyKings Research logo on a chart PNG."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGO = ROOT / "logo" / "buykings research cropped.jpg"
OVERLAY_SCRIPT = ROOT / "scripts" / "overlay_chart_logo.swift"


def run_windows_overlay(
    *,
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    logo_height_ratio: float,
    margin_top_ratio: float,
    margin_top_px: int | None,
    margin_right_ratio: float,
    margin_right_px: int | None,
    opacity: float,
) -> None:
    temp_output = output_path.with_name(output_path.stem + ".logo-tmp" + output_path.suffix)
    env = os.environ.copy()
    env.update(
        {
            "BUYKINGS_INPUT": str(input_path),
            "BUYKINGS_OUTPUT": str(temp_output),
            "BUYKINGS_LOGO": str(logo_path),
            "BUYKINGS_LOGO_HEIGHT_RATIO": str(logo_height_ratio),
            "BUYKINGS_MARGIN_TOP_RATIO": str(margin_top_ratio),
            "BUYKINGS_MARGIN_TOP_PX": str(margin_top_px if margin_top_px is not None else -1),
            "BUYKINGS_MARGIN_RIGHT_RATIO": str(margin_right_ratio),
            "BUYKINGS_MARGIN_RIGHT_PX": str(margin_right_px if margin_right_px is not None else -1),
            "BUYKINGS_OPACITY": str(opacity),
        }
    )
    script = r"""
Add-Type -AssemblyName System.Drawing
[System.Drawing.Bitmap]$base = [System.Drawing.Image]::FromFile($env:BUYKINGS_INPUT)
[System.Drawing.Image]$logo = [System.Drawing.Image]::FromFile($env:BUYKINGS_LOGO)
try {
    $logoHeight = [Math]::Max(1, [int][Math]::Round($base.Height * [double]$env:BUYKINGS_LOGO_HEIGHT_RATIO))
    $logoWidth = [Math]::Max(1, [int][Math]::Round($logoHeight * ($logo.Width / [double]$logo.Height)))
    $marginTopPx = [int]$env:BUYKINGS_MARGIN_TOP_PX
    $marginRightPx = [int]$env:BUYKINGS_MARGIN_RIGHT_PX
    $marginTop = if ($marginTopPx -ge 0) { $marginTopPx } else { [int][Math]::Round($base.Height * [double]$env:BUYKINGS_MARGIN_TOP_RATIO) }
    $marginRight = if ($marginRightPx -ge 0) { $marginRightPx } else { [int][Math]::Round($base.Width * [double]$env:BUYKINGS_MARGIN_RIGHT_RATIO) }
    $originX = [Math]::Max(0, $base.Width - $marginRight - $logoWidth)
    $originY = [Math]::Max(0, $marginTop)

    $graphics = [System.Drawing.Graphics]::FromImage($base)
    try {
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

        $matrix = New-Object System.Drawing.Imaging.ColorMatrix
        $matrix.Matrix33 = [single][double]$env:BUYKINGS_OPACITY
        $attributes = New-Object System.Drawing.Imaging.ImageAttributes
        $attributes.SetColorMatrix($matrix, [System.Drawing.Imaging.ColorMatrixFlag]::Default, [System.Drawing.Imaging.ColorAdjustType]::Bitmap)

        $rect = New-Object System.Drawing.Rectangle($originX, $originY, $logoWidth, $logoHeight)
        $graphics.DrawImage($logo, $rect, 0, 0, $logo.Width, $logo.Height, [System.Drawing.GraphicsUnit]::Pixel, $attributes)
        $base.Save($env:BUYKINGS_OUTPUT, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        if ($attributes) { $attributes.Dispose() }
        $graphics.Dispose()
    }
}
finally {
    $logo.Dispose()
    $base.Dispose()
}
"""
    subprocess.run(
        ["powershell", "-Command", script],
        check=True,
        env=env,
    )
    temp_output.replace(output_path)


def run_swift_overlay(
    *,
    input_path: Path,
    output_path: Path,
    logo_path: Path,
    logo_height_ratio: float,
    margin_top_ratio: float,
    margin_top_px: int | None,
    margin_right_ratio: float,
    margin_right_px: int | None,
    opacity: float,
) -> None:
    module_cache = ROOT / "tmp" / "swift-module-cache"
    module_cache.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["SWIFT_MODULECACHE_PATH"] = str(module_cache)
    env["CLANG_MODULE_CACHE_PATH"] = str(module_cache)

    subprocess.run(
        [
            "swift",
            str(OVERLAY_SCRIPT),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--logo",
            str(logo_path),
            "--logo-height-ratio",
            str(logo_height_ratio),
            "--margin-top-ratio",
            str(margin_top_ratio),
            "--margin-top-px",
            str(margin_top_px if margin_top_px is not None else -1),
            "--margin-right-ratio",
            str(margin_right_ratio),
            "--margin-right-px",
            str(margin_right_px if margin_right_px is not None else -1),
            "--opacity",
            str(opacity),
        ],
        check=True,
        env=env,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input PNG path")
    parser.add_argument("output", nargs="?", help="Output PNG path (defaults to in-place)")
    parser.add_argument("--logo", default=str(DEFAULT_LOGO), help="Logo image path")
    parser.add_argument("--logo-height-ratio", type=float, default=0.10)
    parser.add_argument("--margin-top-ratio", type=float, default=0.03)
    parser.add_argument("--margin-top-px", type=int, help="Override top margin in pixels")
    parser.add_argument("--margin-right-ratio", type=float, default=0.025)
    parser.add_argument("--margin-right-px", type=int, help="Override right margin in pixels")
    parser.add_argument("--opacity", type=float, default=1.0)
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path
    logo_path = Path(args.logo).resolve()

    if not input_path.exists():
        raise SystemExit(f"Missing input image: {input_path}")
    if not logo_path.exists():
        raise SystemExit(f"Missing logo image: {logo_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_kwargs = {
        "input_path": input_path,
        "output_path": output_path,
        "logo_path": logo_path,
        "logo_height_ratio": args.logo_height_ratio,
        "margin_top_ratio": args.margin_top_ratio,
        "margin_top_px": args.margin_top_px,
        "margin_right_ratio": args.margin_right_ratio,
        "margin_right_px": args.margin_right_px,
        "opacity": args.opacity,
    }
    if os.name == "nt" or shutil.which("swift") is None:
        run_windows_overlay(**overlay_kwargs)
    else:
        run_swift_overlay(**overlay_kwargs)

    print(
        json.dumps(
            {
                "ok": True,
                "input": str(input_path),
                "output": str(output_path),
                "logo": str(logo_path),
                "logo_height_ratio": args.logo_height_ratio,
                "margin_top_ratio": args.margin_top_ratio,
                "margin_top_px": args.margin_top_px,
                "margin_right_ratio": args.margin_right_ratio,
                "margin_right_px": args.margin_right_px,
                "opacity": args.opacity,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
