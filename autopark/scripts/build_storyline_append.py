#!/usr/bin/env python3
"""Build an integrated today-misc + image-intel storyline Markdown append."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from caption_visual_assets import PROJECT_ROOT, REPO_ROOT, load_env


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1"


STORYLINE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dashboard_note_ko": {"type": "string"},
        "storylines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "one_liner": {"type": "string"},
                    "why_today": {"type": "string"},
                    "materials": {"type": "array", "items": {"type": "string"}},
                    "suggested_flow": {"type": "array", "items": {"type": "string"}},
                    "opening_script_draft": {"type": "string"},
                    "caveats": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "one_liner",
                    "why_today",
                    "materials",
                    "suggested_flow",
                    "opening_script_draft",
                    "caveats",
                ],
            },
        },
        "sample_alignment_notes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["dashboard_note_ko", "storylines", "sample_alignment_notes"],
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compact_candidates(payload: dict, limit: int) -> list[dict]:
    rows = []
    for candidate in payload.get("candidates", [])[:limit]:
        rows.append(
            {
                "id": candidate.get("id"),
                "source": candidate.get("source_name") or candidate.get("source_id"),
                "headline": candidate.get("headline"),
                "url": candidate.get("url"),
                "published_at": candidate.get("published_at"),
                "summary": candidate.get("summary"),
                "market_hooks": candidate.get("market_hooks"),
                "scores": {
                    "novelty": candidate.get("novelty"),
                    "market_relevance": candidate.get("market_relevance"),
                    "broadcast_fit": candidate.get("broadcast_fit"),
                    "confidence": candidate.get("confidence"),
                },
            }
        )
    return rows


def compact_x(payload: dict, limit: int) -> list[dict]:
    rows = []
    for post in payload.get("posts", [])[:limit]:
        rows.append(
            {
                "id": post.get("id") or post.get("url"),
                "source": post.get("source_name") or post.get("source_id"),
                "url": post.get("url"),
                "created_at": post.get("created_at") or post.get("created_at_inferred"),
                "text": (post.get("text") or "")[:900],
                "image_count": len(post.get("image_refs") or []),
            }
        )
    return rows


def compact_image_intel(payload: dict, limit: int) -> list[dict]:
    rows = []
    for result in payload.get("results", [])[:limit]:
        asset = result.get("asset") or {}
        caption = result.get("caption") or {}
        rows.append(
            {
                "asset_id": asset.get("asset_id"),
                "source": asset.get("source_name"),
                "source_url": asset.get("source_url"),
                "headline": asset.get("headline"),
                "local_path": asset.get("local_path"),
                "status": result.get("status"),
                "visual_title": caption.get("visual_title"),
                "main_claim": caption.get("main_claim_ko"),
                "broadcast_hook": caption.get("broadcast_hook_ko"),
                "related_assets": caption.get("related_assets"),
                "tags": caption.get("storyline_tags"),
                "caveats": caption.get("caveats"),
                "needs_manual_review": caption.get("needs_manual_review"),
            }
        )
    return rows


def sample_outline_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    payload = load_json(path)
    lines = []
    for row in payload.get("blocks", []):
        if row.get("type") in {"heading_1", "heading_2", "heading_3", "quote"}:
            indent = "  " * int(row.get("depth") or 0)
            lines.append(f"{indent}- {row.get('type')}: {row.get('text')}")
    return "\n".join(lines[:120])


def build_prompt(materials: dict, sample_outline: str) -> str:
    return f"""You are drafting a Korean morning-market-broadcast preparation dashboard.

Important framing:
- This is a reverse-engineered dashboard: write as if the host had these materials before making the PPT.
- Do not say "PPT selected this" or "because this appears in the PPT".
- For this trial, do not over-select. Reflect the collected materials broadly and then propose 3 storyline drafts.
- Match the 04.21 sample style if provided: concise news summary, three recommended storylines, each with one-line quote, 선정 이유, 구성 제안.
- Keep caveats visible. Image/chart numbers require manual verification.

04.21 sample outline:
{sample_outline or "- not available locally -"}

Collected materials JSON:
{json.dumps(materials, ensure_ascii=False, indent=2)}
"""


def call_openai(prompt: str, token: str, model: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_storyline_drafts",
                "strict": True,
                "schema": STORYLINE_SCHEMA,
            }
        },
    }
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    parts = []
    for item in raw.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    text = "".join(parts).strip()
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return {"raw_response_id": raw.get("id"), "draft": json.loads(text)}


def link(label: str | None, url: str | None) -> str:
    if not label:
        label = url or "-"
    if url and url.startswith("http"):
        return f"[{label}]({url})"
    return label


def clean_title(value: str | None) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", value or "").strip()


def render_markdown(target_date: str, materials: dict, draft: dict) -> str:
    lines = [
        "# 오늘의 이모저모 통합 초안",
        "",
        f"수집 기준일: `{target_date}`",
        "",
        "> 선별 전 PoC입니다. 현재 수집된 뉴스, X, 특수 사이트 이미지 해석을 고루 반영해 방송 준비자가 훑는 재료판 형태로 구성했습니다.",
        "",
        "## 04.21 샘플 대비 포맷 메모",
        "",
    ]
    for note in draft.get("sample_alignment_notes") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## 주요 뉴스 요약", "", draft.get("dashboard_note_ko") or "-", ""])

    lines.append("## 추천 스토리라인")
    for index, storyline in enumerate(draft.get("storylines") or [], start=1):
        title = clean_title(storyline.get("title"))
        lines.extend(
            [
                "",
                f"### {index}. {title}",
                "",
                f"> {storyline.get('one_liner')}",
                "",
                "#### 선정 이유",
                "",
                f"- {storyline.get('why_today')}",
                "",
                "#### 구성 제안",
                "",
            ]
        )
        for item in storyline.get("suggested_flow") or []:
            lines.append(f"- {item}")
        lines.extend(["", "#### 활용 재료", ""])
        for item in storyline.get("materials") or []:
            lines.append(f"- {item}")
        lines.extend(["", "#### 30초 오프닝 가안", "", storyline.get("opening_script_draft") or "-", "", "#### 주의점", ""])
        for item in storyline.get("caveats") or []:
            lines.append(f"- {item}")

    lines.extend(["", "## 수집 재료", "", "### 뉴스 / 일반 후보", ""])
    for group_name, key in [("Batch A", "batch_a"), ("Batch B", "batch_b")]:
        lines.extend(["", f"#### {group_name}", ""])
        for row in materials.get(key, []):
            lines.append(f"- {link(row.get('headline'), row.get('url'))} ({row.get('source') or '-'})")

    lines.extend(["", "### X 타임라인", ""])
    for row in materials.get("x_posts", []):
        text = " ".join((row.get("text") or "").split())
        lines.append(f"- {link(row.get('source'), row.get('url'))}: {text[:220]}")

    lines.extend(["", "### 이미지 해석 후보", ""])
    for row in materials.get("image_intel", []):
        lines.extend(
            [
                f"#### {row.get('visual_title') or row.get('headline')}",
                "",
                f"- 출처: {link(row.get('source'), row.get('source_url'))}",
                f"- 한 줄 해석: {row.get('main_claim') or '-'}",
                f"- 방송 훅: {row.get('broadcast_hook') or '-'}",
                f"- 주의점: {'; '.join(row.get('caveats') or []) or '-'}",
            ]
        )
        if row.get("local_path"):
            lines.extend(["", f"![{row.get('visual_title') or row.get('headline')}]({row.get('local_path')})"])
        lines.append("")

    lines.extend(
        [
            "## 파이프라인 메모",
            "",
            "- 이번 append는 4/22, 4/23 당일 원자료가 아니라 2026-04-28 수집 PoC를 날짜 문서에 섞어 보는 실험입니다.",
            "- 이미지 해석은 OpenAI vision 1차 판독이며, 숫자/축/출처는 방송 전 수동 검수해야 합니다.",
            "- 다음 단계에서는 후보를 고루 반영하는 방식에서 벗어나, 중복 제거와 선별 점수로 5~8개 핵심 재료만 남기는 흐름이 필요합니다.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=os.environ.get("AUTOPARK_OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--sample-outline", type=Path)
    parser.add_argument("--limit-news", type=int, default=10)
    parser.add_argument("--limit-x", type=int, default=8)
    parser.add_argument("--limit-images", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    token = env.get("OPENAI_API_KEY")
    if not token and not args.dry_run:
        raise SystemExit("Missing OPENAI_API_KEY in environment or .env")

    processed = PROCESSED_DIR / args.date
    materials = {
        "batch_a": compact_candidates(load_json(processed / "today-misc-batch-a-candidates.json"), args.limit_news),
        "batch_b": compact_candidates(load_json(processed / "today-misc-batch-b-candidates.json"), args.limit_news),
        "x_posts": compact_x(load_json(processed / "x-timeline-posts.json"), args.limit_x),
        "image_intel": compact_image_intel(load_json(processed / "image-intel.json"), args.limit_images),
    }
    sample = sample_outline_text(args.sample_outline)

    if args.dry_run:
        draft = {
            "dashboard_note_ko": "dry-run: collected material summary only",
            "storylines": [],
            "sample_alignment_notes": ["dry-run"],
        }
        result = {"status": "dry-run", "draft": draft}
    else:
        result = call_openai(build_prompt(materials, sample), token, args.model, args.timeout)
        draft = result["draft"]

    output = args.output or RUNTIME_NOTION_DIR / args.date / "today-misc-integrated-storylines.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(args.date, materials, draft), encoding="utf-8")

    payload = {
        "ok": True,
        "target_date": args.date,
        "model": args.model,
        "output": str(output),
        "material_counts": {key: len(value) for key, value in materials.items()},
        **result,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
