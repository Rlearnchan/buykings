#!/usr/bin/env python3
"""Render member word2vec period assets from existing CSV outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "exports" / "wepoll-samsung" / "semantic-periods"
REPORT_PATH = ROOT / "projects" / "wepoll-samsung" / "notes" / "member-word2vec-periods.md"
PERIODS = ["2025", "2026", "이벤트주간"]
MEMBERS = ["슈카", "알상무", "니니"]


def setup_plot_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    try:
        from matplotlib import font_manager

        font_names = {f.name for f in font_manager.fontManager.ttflist}
        for candidate in ["AppleGothic", "NanumGothic", "Malgun Gothic"]:
            if candidate in font_names:
                plt.rcParams["font.family"] = candidate
                break
    except Exception:
        pass
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_데이터 부족으로 산출되지 않음_"
    headers = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in df.values.tolist():
        rendered = []
        for cell in row:
            if isinstance(cell, float):
                rendered.append(f"{cell:.4f}")
            else:
                rendered.append(str(cell))
        lines.append("| " + " | ".join(rendered) + " |")
    return "\n".join(lines)


def render_pca() -> Path:
    setup_plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, period in zip(axes, PERIODS):
        df = pd.read_csv(EXPORT_DIR / f"{period}_pca_points.csv")
        for _, row in df.iterrows():
            if row["kind"] == "member":
                ax.scatter(row["x"], row["y"], s=180, color="#c71e1d", zorder=3)
                ax.text(row["x"] + 0.01, row["y"] + 0.01, row["label"], fontsize=10, weight="bold")
            else:
                ax.scatter(row["x"], row["y"], s=45, color="#2b9bc2", alpha=0.8)
                ax.text(row["x"] + 0.01, row["y"] + 0.01, row["label"], fontsize=8)
        ax.set_title(period)
        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
    fig.suptitle("주요 멤버 단어공간 PCA 비교", fontsize=22, weight="bold", y=1.02)
    out = EXPORT_DIR / "member-word2vec-period-pca.png"
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    return out


def write_report(pca_path: Path) -> None:
    parts = [
        "# Member Word2Vec By Period",
        "",
        "기간별 PCA와 similar word top 5를 기록한다.",
        "",
        f"- PCA figure: `{pca_path}`",
        "",
    ]
    for period in PERIODS:
        df = pd.read_csv(EXPORT_DIR / f"{period}_neighbors.csv")
        parts.extend([f"## {period}", ""])
        for member in MEMBERS:
            member_df = df[df["anchor"] == member][["anchor", "neighbor", "cosine"]].reset_index(drop=True)
            parts.extend([f"### {member}", "", md_table(member_df), ""])
    REPORT_PATH.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    pca_path = render_pca()
    write_report(pca_path)
    print(f"wrote_report={REPORT_PATH}")
    print(f"wrote_png={pca_path}")


if __name__ == "__main__":
    main()
