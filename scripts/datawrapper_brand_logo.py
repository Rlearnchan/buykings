#!/usr/bin/env python3
"""Overlay the BuyKings Research logo on a chart PNG."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOGO = ROOT / "logo" / "buykings research cropped.jpg"
OVERLAY_SCRIPT = ROOT / "scripts" / "overlay_chart_logo.swift"


def overlay_with_pillow(input_path: Path, output_path: Path, logo_path: Path, args: argparse.Namespace) -> str:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow is required for cross-platform logo overlay. Install it with `pip install Pillow`."
        ) from exc

    with Image.open(input_path).convert("RGBA") as base, Image.open(logo_path).convert("RGBA") as logo:
        max_height = min(
            int(base.height * args.logo_height_ratio),
            int(args.logo_max_height_px),
            base.height,
        )
        if max_height <= 0:
            raise SystemExit("Computed logo height is not positive.")
        ratio = max_height / logo.height
        logo_size = (max(1, int(logo.width * ratio)), max_height)
        logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
        if args.opacity < 1:
            alpha = logo.getchannel("A").point(lambda value: int(value * args.opacity))
            logo.putalpha(alpha)

        margin_top = args.margin_top_px if args.margin_top_px is not None else int(base.height * args.margin_top_ratio)
        margin_right = args.margin_right_px if args.margin_right_px is not None else int(base.width * args.margin_right_ratio)
        x = max(0, base.width - logo.width - margin_right)
        y = max(0, margin_top)
        base.alpha_composite(logo, (x, y))
        if output_path.suffix.lower() in {".jpg", ".jpeg"}:
            base.convert("RGB").save(output_path)
        else:
            base.save(output_path)
    return "pillow"


def overlay_with_swift(input_path: Path, output_path: Path, logo_path: Path, args: argparse.Namespace) -> str:
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
            str(args.logo_height_ratio),
            "--logo-max-height-px",
            str(args.logo_max_height_px),
            "--margin-top-ratio",
            str(args.margin_top_ratio),
            "--margin-top-px",
            str(args.margin_top_px if args.margin_top_px is not None else -1),
            "--margin-right-ratio",
            str(args.margin_right_ratio),
            "--margin-right-px",
            str(args.margin_right_px if args.margin_right_px is not None else -1),
            "--opacity",
            str(args.opacity),
        ],
        check=True,
        env=env,
    )
    return "swift"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Input PNG path")
    parser.add_argument("output", nargs="?", help="Output PNG path (defaults to in-place)")
    parser.add_argument("--logo", default=str(DEFAULT_LOGO), help="Logo image path")
    parser.add_argument("--logo-height-ratio", type=float, default=0.10)
    parser.add_argument("--logo-max-height-px", type=int, default=96)
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
    if platform.system() == "Darwin" and shutil.which("swift") and not os.environ.get("DATAWRAPPER_LOGO_FORCE_PILLOW"):
        backend = overlay_with_swift(input_path, output_path, logo_path, args)
    else:
        backend = overlay_with_pillow(input_path, output_path, logo_path, args)

    print(
        json.dumps(
            {
                "ok": True,
                "input": str(input_path),
                "output": str(output_path),
                "logo": str(logo_path),
                "logo_height_ratio": args.logo_height_ratio,
                "logo_max_height_px": args.logo_max_height_px,
                "margin_top_ratio": args.margin_top_ratio,
                "margin_top_px": args.margin_top_px,
                "margin_right_ratio": args.margin_right_ratio,
                "margin_right_px": args.margin_right_px,
                "opacity": args.opacity,
                "backend": backend,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
