#!/usr/bin/env python3
"""Render period-specific member word2vec assets as SVG and Markdown using stdlib only."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "wepoll-samsung" / "semantic-periods"
REPORT_PATH = ROOT / "projects" / "wepoll-samsung" / "notes" / "member-word2vec-periods.md"
SVG_PATH = EXPORT_DIR / "member-word2vec-period-pca.svg"
PERIODS = ["2025", "2026", "이벤트주간"]
MEMBERS = {"슈카", "알상무", "니니"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_points(period: str) -> list[dict[str, str]]:
    return read_csv(EXPORT_DIR / f"{period}_pca_points.csv")


def load_neighbors(period: str) -> list[dict[str, str]]:
    return read_csv(EXPORT_DIR / f"{period}_neighbors.csv")


def scale_points(rows: list[dict[str, str]], left: float, top: float, width: float, height: float) -> list[tuple[dict[str, str], float, float]]:
    xs = [float(r["x"]) for r in rows]
    ys = [float(r["y"]) for r in rows]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xspan = xmax - xmin or 1.0
    yspan = ymax - ymin or 1.0
    scaled = []
    for row in rows:
        x = left + 20 + (float(row["x"]) - xmin) / xspan * (width - 40)
        y = top + 20 + (1 - (float(row["y"]) - ymin) / yspan) * (height - 40)
        scaled.append((row, x, y))
    return scaled


def svg_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_svg() -> str:
    width = 1800
    height = 640
    panel_w = 520
    panel_h = 430
    margin_left = 70
    top = 120
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f7f3ee"/>',
        '<text x="900" y="52" text-anchor="middle" font-size="34" font-weight="700" fill="#111">주요 멤버 단어공간 PCA 비교</text>',
        '<text x="900" y="84" text-anchor="middle" font-size="18" fill="#555">2025 / 2026 / 이벤트주간 기준 주요 단어 약 50개와 anchor 주변 유사어 비교</text>',
    ]
    for idx, period in enumerate(PERIODS):
        left = margin_left + idx * 570
        rows = load_points(period)
        parts.append(f'<text x="{left + panel_w/2:.1f}" y="110" text-anchor="middle" font-size="24" font-weight="700" fill="#222">{period}</text>')
        parts.append(f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" fill="white" stroke="#d6d0c8"/>')
        scaled = scale_points(rows, left, top, panel_w, panel_h)
        for row, x, y in scaled:
            label = svg_escape(row["label"])
            if row["kind"] == "member":
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="#c71e1d"/>')
                parts.append(f'<text x="{x + 10:.1f}" y="{y - 10:.1f}" font-size="16" font-weight="700" fill="#c71e1d">{label}</text>')
            else:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#2b9bc2" fill-opacity="0.85"/>')
                parts.append(f'<text x="{x + 6:.1f}" y="{y - 4:.1f}" font-size="11" fill="#3a3a3a">{label}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def md_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "_데이터 부족으로 산출되지 않음_"
    lines = [
        "| anchor | neighbor | cosine |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['anchor']} | {row['neighbor']} | {float(row['cosine']):.4f} |")
    return "\n".join(lines)


def build_report() -> str:
    parts = [
        "# 멤버별 Word2Vec 기간 비교",
        "",
        "2025, 2026, 이벤트주간 기준으로 주요 단어 약 50개의 PCA 위치와 멤버별 유사어 상위 5개를 기록한다.",
        "",
        f"- PCA figure: `{SVG_PATH}`",
        "",
    ]
    for period in PERIODS:
        rows = load_neighbors(period)
        parts.extend([f"## {period}", ""])
        for member in ["슈카", "알상무", "니니"]:
            member_rows = [r for r in rows if r["anchor"] == member]
            parts.extend([f"### {member}", "", md_table(member_rows), ""])
    return "\n".join(parts)


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(build_svg(), encoding="utf-8")
    REPORT_PATH.write_text(build_report(), encoding="utf-8")
    print(f"wrote_svg={SVG_PATH}")
    print(f"wrote_report={REPORT_PATH}")


if __name__ == "__main__":
    main()
