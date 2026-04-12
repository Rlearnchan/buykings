#!/usr/bin/env python3
"""Build period-specific Word2Vec PCA plots and neighbor tables for member terms."""

from __future__ import annotations

import csv
import html
import importlib.util
import os
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gensim.models import Word2Vec


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = ROOT.parent / "wepoll-samsung"
PANIC_SOURCE = ROOT.parent / "wepoll-panic" / "output" / "yearly_hybrid_batch_v4" / "yearly_merged_posts_greed_v8_full.csv"
EVENT_WEEK_SOURCE = Path(
    os.environ.get(
        "EVENT_WEEK_SOURCE",
        ROOT / "projects" / "wepoll-samsung" / "incoming" / "wepoll_stock_eventweek.csv",
    )
)
EXPORT_DIR = ROOT / "exports" / "wepoll-samsung" / "semantic-periods"
REPORT_PATH = ROOT / "projects" / "wepoll-samsung" / "notes" / "member-word2vec-periods.md"
MEMBERS = ["슈카", "알상무", "니니"]
PREFERRED_TERMS = [
    "리서치",
    "예측",
    "정확",
    "도움",
    "신뢰",
    "믿음",
    "조언",
    "분석",
    "유익",
    "친절",
    "매수",
    "매도",
    "수익",
    "손절",
    "삼전",
    "삼성전자",
    "반도체",
    "코스피",
    "환율",
    "금리",
    "인플레이션",
    "위기",
    "경고",
    "투자자",
    "커뮤니티",
    "위폴",
    "알멘",
    "인스타",
    "유튜버",
    "차트공부",
    "매매법",
    "누나",
    "반도체누나",
    "니니누나",
]
JUNK_EXACT = {
    "https",
    "http",
    "com",
    "www",
    "div",
    "class",
    "normal",
    "font",
    "stock",
    "file",
    "start",
    "end",
    "jpg",
    "png",
    "gif",
    "svg",
    "data",
    "ul",
    "li",
    "br",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}
EXTRA_STOPWORDS = {
    "지원자",
    "필자",
    "아침",
    "안녕",
    "실험",
    "진지",
    "개인",
    "설명",
    "문제",
    "의미",
    "필요",
    "구조",
    "조정",
    "유지",
    "원칙",
    "사회",
    "전쟁",
    "말씀",
}

PERIODS = {
    "2025": (date(2025, 3, 28), date(2025, 12, 31)),
    "2026": (date(2026, 1, 1), date(2026, 4, 5)),
    "이벤트주간": (date(2026, 4, 6), date(2026, 4, 11)),
}


def load_upstream_module():
    script_path = UPSTREAM_ROOT / "scripts" / "train_member_word2vec_gensim.py"
    spec = importlib.util.spec_from_file_location("train_member_word2vec_gensim", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


UP = load_upstream_module()
PLACEHOLDER_TO_TERM = dict(getattr(UP, "PLACEHOLDER_TO_TERM", {}))
PLACEHOLDER_TO_MEMBER = dict(getattr(UP, "PLACEHOLDER_TO_MEMBER", {}))
ALL_PLACEHOLDER_MAP = {**PLACEHOLDER_TO_TERM, **PLACEHOLDER_TO_MEMBER}


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


def mention_pattern() -> str:
    aliases = [alias for aliases in UP.ALIASES.values() for alias in aliases]
    return "|".join(re.escape(alias) for alias in aliases)


def clean_raw_text(text: str) -> str:
    cleaned = html.unescape(str(text))
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"www\.\S+", " ", cleaned)
    cleaned = re.sub(r"[A-Za-z0-9_./:-]{8,}", " ", cleaned)
    cleaned = re.sub(r"&[a-zA-Z]+;", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def decode_placeholders(token: str) -> str:
    out = token
    for placeholder, replacement in sorted(ALL_PLACEHOLDER_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        out = out.replace(placeholder, replacement)
    return out


def is_valid_token(token: str) -> bool:
    if token in MEMBERS:
        return True
    if len(token) < 2:
        return False
    if token in JUNK_EXACT or token in EXTRA_STOPWORDS or token in getattr(UP, "STOPWORDS", set()):
        return False
    if re.search(r"[<>_=#]", token):
        return False
    if re.fullmatch(r"\d+", token):
        return False
    if re.search(r"\d{2,}", token):
        return False
    if re.fullmatch(r"[A-Za-z]+", token):
        return False
    if re.search(r"[A-Za-z]{2,}", token):
        return False
    if not re.search(r"[가-힣]", token):
        return False
    if token.endswith(("참고", "토큰")):
        return False
    return True


def load_period_texts() -> dict[str, list[str]]:
    pattern = mention_pattern()
    out = {name: [] for name in PERIODS}

    df = pd.read_csv(PANIC_SOURCE, low_memory=False, usecols=["title", "body_text", "created_at"])
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    text_series = (df["title"].fillna("").astype(str) + " " + df["body_text"].fillna("").astype(str)).map(clean_raw_text)
    df = df[text_series.str.contains(pattern, na=False, regex=True)].copy()
    df["text"] = text_series.loc[df.index]
    for name, (start, end) in PERIODS.items():
        if name == "이벤트주간":
            continue
        mask = (df["created_at"].dt.date >= start) & (df["created_at"].dt.date <= end)
        out[name] = df.loc[mask, "text"].tolist()

    csv.field_size_limit(10**9)
    with EVENT_WEEK_SOURCE.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            created = row.get("작성시각", "")
            if not created:
                continue
            current_date = pd.to_datetime(created, errors="coerce")
            if pd.isna(current_date):
                continue
            d = current_date.date()
            if d < PERIODS["이벤트주간"][0] or d > PERIODS["이벤트주간"][1]:
                continue
            text = clean_raw_text(f"{row.get('제목','')} {row.get('본문','')}")
            if pd.Series([text]).str.contains(pattern, na=False, regex=True).iloc[0]:
                out["이벤트주간"].append(text)
    return out


def tokenize_corpus(texts: Iterable[str]) -> list[list[str]]:
    corpus: list[list[str]] = []
    for text in texts:
        raw_tokens = UP.tokenize(text)
        tokens = []
        for token in raw_tokens:
            normalized = decode_placeholders(token)
            if is_valid_token(normalized):
                tokens.append(normalized)
        if tokens:
            corpus.append(tokens)
    return corpus


def train_model(corpus: list[list[str]]) -> Word2Vec:
    return Word2Vec(
        sentences=corpus,
        vector_size=50,
        window=5,
        min_count=2,
        workers=1,
        sg=1,
        epochs=30,
        seed=42,
    )


def period_neighbors(model: Word2Vec) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for member in MEMBERS:
        rows = []
        if member in model.wv:
            for neighbor, score in model.wv.most_similar(member, topn=5):
                rows.append({"anchor": member, "neighbor": neighbor, "cosine": float(score)})
        tables[member] = pd.DataFrame(rows)
    return tables


def top_labels(model: Word2Vec, corpus: list[list[str]], tables: dict[str, pd.DataFrame], topn: int = 70) -> list[str]:
    counts = Counter(token for doc in corpus for token in doc if token in model.wv)
    labels = []
    for member in MEMBERS:
        if member in model.wv:
            labels.append(member)
        if not tables[member].empty:
            labels.extend(tables[member]["neighbor"].tolist())
    for token in PREFERRED_TERMS:
        if token in model.wv and token not in labels:
            labels.append(token)
    for token, _ in counts.most_common(topn):
        if token not in labels:
            labels.append(token)
    return labels[:topn]


def compute_pca_points(model: Word2Vec, labels: list[str]) -> pd.DataFrame:
    vectors = np.array([model.wv[label] for label in labels], dtype=float)
    centered = vectors - vectors.mean(axis=0, keepdims=True)
    u, s, _ = np.linalg.svd(centered, full_matrices=False)
    coords = u[:, :2] * s[:2]
    return pd.DataFrame(
        {
            "label": labels,
            "x": coords[:, 0],
            "y": coords[:, 1],
            "kind": ["member" if label in MEMBERS else "token" for label in labels],
        }
    )


def plot_pca_panels(period_frames: dict[str, pd.DataFrame]) -> Path:
    setup_plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, period in zip(axes, ["2025", "2026", "이벤트주간"]):
        df = period_frames[period]
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


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    texts_by_period = load_period_texts()
    report_parts = ["# Member Word2Vec By Period", "", "기간별 PCA와 similar word top 5를 기록한다.", ""]
    pca_frames: dict[str, pd.DataFrame] = {}

    for period in ["2025", "2026", "이벤트주간"]:
        corpus = tokenize_corpus(texts_by_period[period])
        if not corpus:
            continue
        model = train_model(corpus)
        tables = period_neighbors(model)
        labels = top_labels(model, corpus, tables, topn=70)
        pca = compute_pca_points(model, labels)
        pca.to_csv(EXPORT_DIR / f"{period}_pca_points.csv", index=False)
        pca_frames[period] = pca

        period_table = pd.concat(
            [df.assign(period=period) for df in tables.values() if not df.empty],
            ignore_index=True,
        )
        if not period_table.empty:
            period_table.to_csv(EXPORT_DIR / f"{period}_neighbors.csv", index=False)

        report_parts.extend([f"## {period}", "", f"- 문서 수: {len(corpus)}", f"- vocab size: {len(model.wv)}", ""])
        for member in MEMBERS:
            report_parts.extend([f"### {member}", "", md_table(tables[member]), ""])

    if pca_frames:
        pca_path = plot_pca_panels(pca_frames)
        report_parts.extend(["## PCA Figure", "", f"- PNG: `{pca_path}`", ""])

    REPORT_PATH.write_text("\n".join(report_parts), encoding="utf-8")
    print(f"wrote_report={REPORT_PATH}")
    os._exit(0)


if __name__ == "__main__":
    main()
