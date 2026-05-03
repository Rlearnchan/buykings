#!/usr/bin/env python3
"""Extract a slide outline from a Buykings broadcast PPTX without launching PowerPoint."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import zipfile
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "runtime"

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

BOILERPLATE = {
    "economy l finance l politics l world",
    "the buykings times",
    "economy",
    "finance",
    "politics",
    "world",
    "l",
}


def clean(value: object, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def default_ppt_path(target_date: str) -> Path | None:
    mmdd = datetime.fromisoformat(target_date).strftime("%m%d")
    candidates = sorted(PROJECT_ROOT.glob(f"*{mmdd}*.pptx")) + sorted(PROJECT_ROOT.glob(f"*{mmdd}*.ppt"))
    return candidates[0] if candidates else None


def slide_order(zip_file: zipfile.ZipFile) -> list[str]:
    try:
        presentation = ET.fromstring(zip_file.read("ppt/presentation.xml"))
        rels = ET.fromstring(zip_file.read("ppt/_rels/presentation.xml.rels"))
    except (KeyError, ET.ParseError):
        return sorted(
            [name for name in zip_file.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name)],
            key=lambda name: int(re.search(r"(\d+)", name).group(1)),
        )
    rel_map = {
        rel.attrib.get("Id"): rel.attrib.get("Target", "")
        for rel in rels.findall("rel:Relationship", NS)
    }
    slides: list[str] = []
    for node in presentation.findall(".//p:sldId", NS):
        rel_id = node.attrib.get(f"{{{NS['r']}}}id")
        target = rel_map.get(rel_id)
        if not target:
            continue
        path = posixpath.normpath(posixpath.join("ppt", target))
        if path in zip_file.namelist():
            slides.append(path)
    return slides


def paragraph_texts(slide_xml: bytes) -> list[str]:
    root = ET.fromstring(slide_xml)
    rows: list[str] = []
    for para in root.findall(".//a:p", NS):
        text = clean("".join(node.text or "" for node in para.findall(".//a:t", NS)))
        if text:
            rows.append(text)
    return rows


def choose_title(lines: list[str]) -> str:
    meaningful = []
    for line in lines:
        lowered = clean(line).lower()
        if lowered in BOILERPLATE:
            continue
        if re.fullmatch(r"[\d\s/:.,()-]+", lowered):
            continue
        meaningful.append(line)
    if not meaningful:
        return lines[0] if lines else "untitled"
    if len(meaningful) >= 3 and len(clean(" ".join(meaningful[:3]))) <= 42:
        return clean(" ".join(meaningful[:3]), 90)
    if len(meaningful) >= 2 and len(meaningful[0]) <= 4 and len(meaningful[1]) <= 12:
        return clean(" ".join(meaningful[:2]), 90)
    return clean(meaningful[0], 90)


def classify_visual_role(title: str, lines: list[str]) -> str:
    blob = clean(" ".join([title, *lines])).lower()
    if "주요 지수" in blob or "index" in blob:
        return "index_chart"
    if "히트맵" in blob or "heatmap" in blob:
        return "sector_heatmap"
    if "10년물" in blob or "국채금리" in blob or "treasury" in blob or "yield" in blob:
        return "rates_chart"
    if "wti" in blob or "브렌트" in blob or "유가" in blob or "oil" in blob:
        return "oil_chart"
    if "달러" in blob or "dxy" in blob or "원달러" in blob or "usd/krw" in blob:
        return "fx_chart"
    if "비트코인" in blob or "bitcoin" in blob or "btc" in blob:
        return "crypto_chart"
    if "실적발표" in blob or "실적 발표" in blob or "earnings calendar" in blob:
        return "earnings_calendar"
    if any(token in blob for token in ["eps", "매출", "가이던스", "영업이익", "실적"]):
        return "earnings_card"
    if "fomc" in blob or "fmc" in blob or "연준" in blob:
        return "fomc_statement"
    if "fedwatch" in blob or "금리 확률" in blob:
        return "fedwatch_chart"
    if any(token in blob for token in ["meme", "머스크", "알트만", "트럼프", "화성"]):
        return "meme_or_fun_slide"
    if len(lines) >= 4 and not any(token in blob for token in ["chart", "차트", "히트맵"]):
        return "educational_slide"
    return "article_screenshot"


def count_image_rels(zip_file: zipfile.ZipFile, slide_name: str) -> int:
    rel_path = f"ppt/slides/_rels/{Path(slide_name).name}.rels"
    if rel_path not in zip_file.namelist():
        return 0
    try:
        rels = ET.fromstring(zip_file.read(rel_path))
    except ET.ParseError:
        return 0
    return sum(
        1
        for rel in rels.findall("rel:Relationship", NS)
        if "image" in (rel.attrib.get("Type") or "").lower()
    )


def extract_outline(ppt_path: Path, target_date: str) -> dict:
    slides: list[dict] = []
    with zipfile.ZipFile(ppt_path) as zip_file:
        for index, slide_name in enumerate(slide_order(zip_file), start=1):
            lines = paragraph_texts(zip_file.read(slide_name))
            title = choose_title(lines)
            visual_role = classify_visual_role(title, lines)
            slides.append(
                {
                    "slide_number": index,
                    "slide_id": f"slide-{index:03d}",
                    "title": title,
                    "text": clean(" ".join(lines), 800),
                    "text_lines": lines[:24],
                    "visual_asset_role": visual_role,
                    "image_count": count_image_rels(zip_file, slide_name),
                    "use_as_slide": True,
                }
            )
    return {
        "ok": True,
        "target_date": target_date,
        "source_path": str(ppt_path),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "slide_count": len(slides),
        "slides": slides,
    }


def render_markdown(payload: dict) -> str:
    lines = [
        f"# PPT Outline - {payload.get('target_date')}",
        "",
        f"- source: `{payload.get('source_path')}`",
        f"- slide_count: `{payload.get('slide_count')}`",
        "",
    ]
    for slide in payload.get("slides") or []:
        lines.extend(
            [
                f"## {slide.get('slide_number')}. {slide.get('title')}",
                "",
                f"- role: `{slide.get('visual_asset_role')}`",
                f"- images: `{slide.get('image_count')}`",
            ]
        )
        body = [line for line in slide.get("text_lines") or [] if line != slide.get("title")]
        if body:
            lines.append(f"- text: {clean(' / '.join(body[:4]), 220)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--ppt", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ppt_path = args.ppt or default_ppt_path(args.date)
    if not ppt_path or not ppt_path.exists():
        print_json({"ok": False, "error": "missing_ppt", "date": args.date})
        return 1
    output_dir = args.output_dir or (RUNTIME_DIR / "broadcast" / args.date)
    payload = extract_outline(ppt_path, args.date)
    json_path = output_dir / "ppt-outline.json"
    md_path = output_dir / "ppt-outline.md"
    if not args.dry_run:
        write_json(json_path, payload)
        write_text(md_path, render_markdown(payload))
    print_json(
        {
            "ok": True,
            "date": args.date,
            "source": str(ppt_path),
            "slide_count": payload.get("slide_count"),
            "json": str(json_path),
            "markdown": str(md_path),
            "dry_run": args.dry_run,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
