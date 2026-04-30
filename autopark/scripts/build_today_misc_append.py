#!/usr/bin/env python3
"""Build a compact Notion append Markdown from current today-misc outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def one_line(value: str, limit: int = 260) -> str:
    text = " ".join((value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def render_candidate(candidate: dict, index: int) -> list[str]:
    hooks = ", ".join(candidate.get("market_hooks") or []) or "-"
    tickers = ", ".join(candidate.get("tickers") or []) or "-"
    return [
        f"### 후보 {index}. {candidate.get('headline', '-')}",
        "",
        f"- 출처: [{candidate.get('source_name', candidate.get('source_id', '-'))}]({candidate.get('url', '')})",
        f"- 날짜: {candidate.get('published_at') or '-'}",
        f"- 감지 키워드: {hooks}",
        f"- 티커 후보: {tickers}",
        "",
    ]


def render_post(post: dict, index: int) -> list[str]:
    text = one_line(post.get("text", ""), 500)
    return [
        f"### X 후보 {index}. {post.get('source_name', post.get('source_id', '-'))}",
        "",
        f"- URL: {post.get('url') or post.get('account_url') or '-'}",
        f"- 시간: {post.get('created_at') or post.get('relative_time') or post.get('created_at_inferred') or '-'}",
        f"- 이미지: {post.get('image_count', 0)}",
        f"- 내용: {text}",
        "",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-a", type=int, default=8)
    parser.add_argument("--max-b", type=int, default=8)
    parser.add_argument("--max-x", type=int, default=6)
    args = parser.parse_args()

    processed_dir = PROJECT_ROOT / "data" / "processed" / args.date
    output = args.output or PROJECT_ROOT / "runtime" / "notion" / args.date / "today-misc-poc-append.md"
    batch_a = load_json(processed_dir / "today-misc-batch-a-candidates.json")
    batch_b = load_json(processed_dir / "today-misc-batch-b-candidates.json")
    x_posts = load_json(processed_dir / "x-timeline-posts.json")

    lines = [
        "# 오늘의 이모저모 자동 수집 PoC",
        "",
        f"수집 기준일: {args.date}",
        "",
        "아래 내용은 역구성 문서 제작 과정에서 자동 수집 파이프라인을 검증하기 위한 실험 블록입니다. "
        "4/22, 4/23 당일 자료로 확정된 내용이 아니라, 현재 수집기가 어떤 후보를 뽑는지 확인하기 위한 샘플입니다.",
        "",
        "## Batch A. 뉴스 골격",
        "",
    ]
    for index, candidate in enumerate((batch_a.get("candidates") or [])[: args.max_a], start=1):
        lines.extend(render_candidate(candidate, index))

    lines.extend(["## Batch B. 특수 사이트/리서치", ""])
    for index, candidate in enumerate((batch_b.get("candidates") or [])[: args.max_b], start=1):
        lines.extend(render_candidate(candidate, index))

    lines.extend(["## X 타임라인", ""])
    for index, post in enumerate((x_posts.get("posts") or [])[: args.max_x], start=1):
        lines.extend(render_post(post, index))

    lines.extend(
        [
            "## 수집 상태 메모",
            "",
            "- CNBC, TradingView, Yahoo Finance는 Batch A 후보 생성 가능.",
            "- Isabelnet과 FactSet은 Batch B 후보 생성 가능.",
            "- X는 browser collector MVP로 일부 계정 후보 수집 가능. 계정별 공개 노출 차이가 있어 로그인 profile 또는 API 검토 필요.",
            "- Reuters, Advisor Perspectives는 현재 일반 HTTP 수집에서 막힘.",
            "",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
