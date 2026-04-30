#!/usr/bin/env python3
"""Select broadcast-worthy materials and draft three storylines."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

from caption_visual_assets import PROJECT_ROOT, REPO_ROOT, load_env


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1"


SELECTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dashboard_summary_bullets": {"type": "array", "items": {"type": "string"}},
        "selected_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "type": {"type": "string"},
                    "selection_reason": {"type": "string"},
                    "storyline_fit": {"type": "string"},
                    "verification_note": {"type": "string"},
                    "visual_local_path": {"type": "string"},
                },
                "required": [
                    "id",
                    "title",
                    "source",
                    "url",
                    "type",
                    "selection_reason",
                    "storyline_fit",
                    "verification_note",
                    "visual_local_path",
                ],
            },
        },
        "storylines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "one_liner": {"type": "string"},
                    "why_selected": {"type": "string"},
                    "selected_item_ids": {"type": "array", "items": {"type": "string"}},
                    "slide_flow": {"type": "array", "items": {"type": "string"}},
                    "opening_script_draft": {"type": "string"},
                    "verification_notes": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "title",
                    "one_liner",
                    "why_selected",
                    "selected_item_ids",
                    "slide_flow",
                    "opening_script_draft",
                    "verification_notes",
                ],
            },
        },
        "deferred_patterns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["dashboard_summary_bullets", "selected_items", "storylines", "deferred_patterns"],
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compact_text(value: str | None, limit: int = 700) -> str:
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def news_items(payload: dict, limit: int) -> list[dict]:
    rows = []
    for candidate in payload.get("candidates", [])[:limit]:
        rows.append(
            {
                "id": candidate.get("id"),
                "type": "news",
                "source": candidate.get("source_name") or candidate.get("source_id"),
                "title": candidate.get("headline"),
                "url": candidate.get("url"),
                "published_at": candidate.get("published_at"),
                "summary": compact_text(candidate.get("summary")),
                "market_hooks": candidate.get("market_hooks") or [],
                "tickers": candidate.get("tickers") or [],
                "score": candidate.get("score"),
                "visual_local_path": "",
            }
        )
    return rows


def x_items(payload: dict, limit: int) -> list[dict]:
    rows = []
    for post in payload.get("posts", [])[:limit]:
        text = compact_text(post.get("text"), 900)
        rows.append(
            {
                "id": post.get("id") or post.get("url"),
                "type": "x_social",
                "source": post.get("source_name") or post.get("source_id"),
                "title": text[:120] or post.get("url"),
                "url": post.get("url") or post.get("account_url"),
                "published_at": post.get("created_at") or post.get("created_at_inferred"),
                "summary": text,
                "market_hooks": [],
                "tickers": [],
                "score": None,
                "visual_local_path": (post.get("image_refs") or [{}])[0].get("local_path", "") if post.get("image_refs") else "",
            }
        )
    return rows


def visual_items(payload: dict, limit: int) -> list[dict]:
    rows = []
    for card in payload.get("cards", [])[:limit]:
        vision = card.get("vision_optional") or {}
        summary = card.get("description") or vision.get("main_claim_ko") or card.get("image_alt")
        rows.append(
            {
                "id": card.get("id"),
                "type": "visual_card",
                "source": card.get("source_name") or card.get("source_id"),
                "title": card.get("title"),
                "url": card.get("url"),
                "published_at": card.get("published_at"),
                "summary": compact_text(summary, 900),
                "image_alt": card.get("image_alt"),
                "market_hooks": card.get("market_hooks") or [],
                "tickers": card.get("tickers") or [],
                "score": (card.get("scores") or {}).get("score"),
                "visual_local_path": card.get("local_path") or "",
                "vision_available": vision.get("available", False),
            }
        )
    return rows


def gather_materials(target_date: str, limit_news: int, limit_x: int, limit_visuals: int) -> list[dict]:
    processed = PROCESSED_DIR / target_date
    rows = []
    rows.extend(news_items(load_json(processed / "today-misc-batch-a-candidates.json"), limit_news))
    rows.extend(news_items(load_json(processed / "today-misc-batch-b-candidates.json"), limit_news))
    rows.extend(x_items(load_json(processed / "x-timeline-posts.json"), limit_x))
    rows.extend(visual_items(load_json(processed / "visual-cards.json"), limit_visuals))
    seen = set()
    deduped = []
    for row in rows:
        key = (row.get("title"), row.get("url"), row.get("type"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def sample_outline_text(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    payload = load_json(path)
    lines = []
    for row in payload.get("blocks", []):
        if row.get("type") in {"heading_1", "heading_2", "heading_3", "quote"}:
            lines.append(f"- {row.get('type')}: {row.get('text')}")
    return "\n".join(lines[:100])


def build_prompt(materials: list[dict], sample_outline: str, selected_count: int) -> str:
    return f"""You are selecting materials for a Korean morning-market-broadcast dashboard.

Framing:
- This is a pre-PPT preparation dashboard, not a post-hoc PPT explanation.
- Select {selected_count} strong materials from the candidate list.
- Every ID in every storyline.selected_item_ids must be one of selected_items[].id. Never cite unselected material IDs in storylines.
- Use the model primarily for selection and storyline design, not for restating every chart.
- Prefer materials that connect several sources into a broadcastable market story.
- Keep visual cards lightweight: use their source description/alt as evidence; ask for manual review when numbers are uncertain.
- Match the 04.21 sample rhythm: 주요 뉴스 요약, 추천 스토리라인 3개, each with quote, 선정 이유, 구성 제안.
- Do not invent URLs, ids, or precise chart numbers beyond the provided material.

04.21 sample outline:
{sample_outline or "- not available -"}

Candidate materials:
{json.dumps(materials, ensure_ascii=False, indent=2)}
"""


def call_openai(prompt: str, token: str, model: str, timeout: int) -> dict:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_material_selection_storylines",
                "strict": True,
                "schema": SELECTION_SCHEMA,
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
    return {"raw_response_id": raw.get("id"), "selection": json.loads(text)}


def repair_selection(selection: dict, materials: list[dict]) -> dict:
    material_lookup = {item.get("id"): item for item in materials}
    for item in selection.get("selected_items", []):
        original = material_lookup.get(item.get("id"))
        if not original:
            continue
        for key in ["url", "visual_local_path", "type"]:
            item[key] = original.get(key) or ""
        if original.get("source"):
            item["source"] = original["source"]

    selected_ids = {item.get("id") for item in selection.get("selected_items", [])}
    for storyline in selection.get("storylines", []):
        if "opening_script_draft" in storyline:
            storyline["opening_script_draft"] = storyline["opening_script_draft"].replace(
                "러시아-이란 긴장감",
                "이란발 지정학 긴장",
            )
        original_ids = storyline.get("selected_item_ids", [])
        kept_ids = [item_id for item_id in original_ids if item_id in selected_ids]
        dropped_ids = [item_id for item_id in original_ids if item_id not in selected_ids]
        storyline["selected_item_ids"] = kept_ids
        if dropped_ids:
            notes = storyline.setdefault("verification_notes", [])
            notes.append(f"자동 후처리: 선별 카드 밖 참조 제거 ({', '.join(dropped_ids)})")
    return selection


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url.startswith("http") else label


def clean_title(value: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", value or "").strip()


def render_markdown(target_date: str, selection: dict) -> str:
    selected = {item["id"]: item for item in selection.get("selected_items", [])}
    lines = [
        "# 오늘의 이모저모 선별 및 스토리라인 v2",
        "",
        f"수집 기준일: `{target_date}`",
        "",
        "> 모델은 캡션 작성보다 선별과 스토리 구상에 집중합니다. 이미지 설명은 사이트 원문/alt/주변 설명을 우선 사용합니다.",
        "",
        "## 주요 뉴스 요약",
        "",
    ]
    for item in selection.get("dashboard_summary_bullets", []):
        lines.append(f"- {item}")

    lines.extend(["", "## 추천 스토리라인", ""])
    for index, storyline in enumerate(selection.get("storylines", []), start=1):
        lines.extend(
            [
                f"### {index}. {clean_title(storyline.get('title', ''))}",
                "",
                f"> {storyline.get('one_liner', '')}",
                "",
                "#### 선정 이유",
                "",
                f"- {storyline.get('why_selected', '')}",
                "",
                "#### 구성 제안",
                "",
            ]
        )
        for flow in storyline.get("slide_flow", []):
            lines.append(f"- {flow}")
        lines.extend(["", "#### 연결 자료", ""])
        for material_id in storyline.get("selected_item_ids", []):
            material = selected.get(material_id)
            if material:
                lines.append(f"- `{material_id}` {link(material.get('title', material_id), material.get('url', ''))}")
            else:
                lines.append(f"- `{material_id}`")
        lines.extend(["", "#### 30초 오프닝 가안", "", storyline.get("opening_script_draft", ""), "", "#### 확인 필요", ""])
        for note in storyline.get("verification_notes", []):
            lines.append(f"- {note}")
        lines.append("")

    lines.extend(["## 채택 재료 카드", ""])
    for item in selection.get("selected_items", []):
        lines.extend(
            [
                f"### {item.get('title')}",
                "",
                f"- ID: `{item.get('id')}`",
                f"- 유형: `{item.get('type')}`",
                f"- 출처: {link(item.get('source', '-'), item.get('url', ''))}",
                f"- 선정 이유: {item.get('selection_reason')}",
                f"- 스토리 연결: {item.get('storyline_fit')}",
                f"- 확인 필요: {item.get('verification_note')}",
            ]
        )
        if item.get("visual_local_path"):
            lines.extend(["", f"![{item.get('title')}]({item.get('visual_local_path')})"])
        lines.append("")

    lines.extend(["## 보류 패턴", ""])
    for item in selection.get("deferred_patterns", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=os.environ.get("AUTOPARK_OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--sample-outline", type=Path)
    parser.add_argument("--limit-news", type=int, default=12)
    parser.add_argument("--limit-x", type=int, default=8)
    parser.add_argument("--limit-visuals", type=int, default=8)
    parser.add_argument("--selected-count", type=int, default=7)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    token = env.get("OPENAI_API_KEY")
    if not token and not args.dry_run:
        raise SystemExit("Missing OPENAI_API_KEY in environment or .env")

    materials = gather_materials(args.date, args.limit_news, args.limit_x, args.limit_visuals)
    if args.dry_run:
        result = {"status": "dry-run", "selection": {"dashboard_summary_bullets": [], "selected_items": [], "storylines": [], "deferred_patterns": []}}
    else:
        result = call_openai(
            build_prompt(materials, sample_outline_text(args.sample_outline), args.selected_count),
            token,
            args.model,
            args.timeout,
        )
        result["selection"] = repair_selection(result["selection"], materials)

    processed_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    processed_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "model": args.model,
        "material_count": len(materials),
        "materials": materials,
        **result,
    }
    (processed_dir / "storyline-selection-v2.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (notion_dir / "storyline-selection-v2.md").write_text(render_markdown(args.date, result["selection"]), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
