#!/usr/bin/env python3
"""Build an LLM-authored editorial brief for the Autopark dashboard."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"


EDITORIAL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["daily_thesis", "editorial_summary", "storylines"],
    "properties": {
        "daily_thesis": {"type": "string"},
        "editorial_summary": {"type": "string"},
        "storylines": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title",
                    "recommendation_stars",
                    "rating_reason",
                    "hook",
                    "why_now",
                    "core_argument",
                    "evidence_to_use",
                    "evidence_to_drop",
                    "slide_order",
                    "talk_track",
                    "counterpoint",
                ],
                "properties": {
                    "title": {"type": "string"},
                    "recommendation_stars": {"type": "integer", "minimum": 1, "maximum": 3},
                    "rating_reason": {"type": "string"},
                    "hook": {"type": "string"},
                    "why_now": {"type": "string"},
                    "core_argument": {"type": "string"},
                    "evidence_to_use": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["item_id", "title", "reason"],
                            "properties": {
                                "item_id": {"type": "string"},
                                "title": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "evidence_to_drop": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["item_id", "title", "reason"],
                            "properties": {
                                "item_id": {"type": "string"},
                                "title": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "slide_order": {"type": "array", "items": {"type": "string"}},
                    "talk_track": {"type": "string"},
                    "counterpoint": {"type": "string"},
                },
            },
        },
    },
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact_text(value: object, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def title_of(item: dict) -> str:
    return compact_text(item.get("title") or item.get("headline") or item.get("summary") or item.get("id"), 120)


def source_of(item: dict) -> str:
    return compact_text(item.get("source") or item.get("type") or item.get("publisher") or "", 80)


def candidate_rank(item: dict) -> tuple[float, int, int, str]:
    score = float(item.get("score") or item.get("final_score") or 0)
    visual = 1 if item.get("visual_local_path") or item.get("image_refs") else 0
    source_count = len(set(item.get("sources") or [item.get("source") or ""]))
    return (score, visual, source_count, title_of(item))


def compact_candidate(item: dict) -> dict:
    return {
        "id": str(item.get("id") or ""),
        "title": title_of(item),
        "source": source_of(item),
        "url": item.get("url") or "",
        "published_at": item.get("published_at") or item.get("captured_at") or "",
        "score": item.get("score") or item.get("final_score") or 0,
        "theme_keys": item.get("theme_keys") or item.get("market_hooks") or [],
        "summary": compact_text(item.get("summary") or item.get("text") or item.get("selection_reason"), 520),
        "visual_local_path": item.get("visual_local_path") or "",
    }


def compact_finviz_item(item: dict) -> dict:
    return {
        "ticker": item.get("ticker") or "",
        "title": title_of(item),
        "screenshot_path": item.get("screenshot_path") or "",
        "quote_summary": [compact_text(row, 160) for row in (item.get("quote_summary") or [])[:3]],
        "news": [
            {
                "time": compact_text(row.get("time"), 30),
                "headline": compact_text(row.get("headline"), 160),
                "url": row.get("url") or "",
            }
            for row in (item.get("news") or [])[:4]
        ],
    }


def load_recent_briefs(target_date: str, days: int = 7) -> list[dict]:
    current = parse_date(target_date)
    briefs = []
    for offset in range(1, days + 1):
        day = (current - timedelta(days=offset)).isoformat()
        brief = load_json(PROCESSED_DIR / day / "editorial-brief.json")
        if brief:
            briefs.append(
                {
                    "date": day,
                    "daily_thesis": brief.get("daily_thesis") or "",
                    "titles": [story.get("title") for story in brief.get("storylines", []) if story.get("title")],
                }
            )
    return briefs


def load_recent_broadcast_feedback(target_date: str, days: int = 7) -> list[dict]:
    current = parse_date(target_date)
    rows = []
    for offset in range(1, days + 1):
        day = (current - timedelta(days=offset)).isoformat()
        folder = RUNTIME_DIR / "broadcast" / day
        if not folder.exists():
            continue
        snippets = []
        paths = [path for path in sorted(folder.glob("*")) if path.suffix.lower() in {".md", ".txt"}]
        preferred = [path for path in paths if any(token in path.name.lower() for token in ["retrospective", "feedback", "review"])]
        fallback = [path for path in paths if path not in preferred and not any(token in path.name.lower() for token in ["host-segment", "transcript"])]
        for path in [*preferred, *fallback]:
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = compact_text(path.read_text(encoding="utf-8", errors="replace"), 900)
            if text:
                snippets.append({"file": path.name, "text": text})
        if snippets:
            rows.append({"date": day, "files": snippets[:4]})
    return rows


def build_input_payload(target_date: str, max_candidates: int) -> dict:
    processed = PROCESSED_DIR / target_date
    radar = load_json(processed / "market-radar.json")
    candidates = sorted(radar.get("candidates") or [], key=candidate_rank, reverse=True)[:max_candidates]
    finviz = load_json(processed / "finviz-feature-stocks.json")
    visuals = load_json(processed / "visual-cards.json")
    return {
        "date": target_date,
        "policy": {
            "selection_style": "strong_selective",
            "minimum_storylines": 3,
            "maximum_storylines": 5,
            "do_not_pad_to_five": True,
            "operation_mode": os.environ.get("AUTOPARK_OPERATION_MODE") or "daily_broadcast",
            "expected_broadcast": os.environ.get("AUTOPARK_EXPECTED_BROADCAST", "1") != "0",
            "operation_note": os.environ.get("AUTOPARK_OPERATION_NOTE") or "",
        },
        "market_radar_storylines": radar.get("storylines") or [],
        "candidates": [compact_candidate(item) for item in candidates if item.get("id")],
        "finviz_feature_stocks": [compact_finviz_item(item) for item in (finviz.get("items") or [])[:10]],
        "visual_cards": [
            {
                "id": item.get("id") or item.get("title") or "",
                "title": title_of(item),
                "summary": compact_text(item.get("summary") or item.get("caption") or "", 220),
                "path": item.get("local_path") or item.get("visual_local_path") or "",
            }
            for item in (visuals.get("cards") or visuals.get("items") or [])[:16]
        ],
        "recent_briefs": load_recent_briefs(target_date),
        "recent_broadcast_feedback": load_recent_broadcast_feedback(target_date),
    }


def build_prompt(payload: dict) -> str:
    return f"""You are the editorial lead for a Korean morning markets broadcast.

Write an editorial brief, not a mechanical summary.

Rules:
- Use only the provided candidates and evidence IDs.
- Do not invent facts, prices, dates, or claims outside the evidence.
- Select 3 to 5 storylines. Do not pad to 5 if only 3 are strong.
- Merge overlapping stories instead of splitting the same theme twice.
- Each storyline must be a usable broadcast segment with a hook, why-now, argument, evidence, talk track, and counterpoint.
- Prefer Korean that sounds like a human market editor, not a scoring system.
- Do not mention internal scoring, clustering, source-count logic, or "same-direction signals".
- Put weak-but-related material into evidence_to_drop with a reason.
- Every evidence_to_use item_id must come from candidates[].id.
- Rating uses 1 to 3 stars: 3 = lead segment, 2 = useful segment, 1 = backup only.
- If recent_broadcast_feedback is present, infer what the human actually used and adjust today's selection style accordingly.
- Treat broadcast feedback as preference/format guidance, not as a source for new market facts.
- If policy.operation_mode is no_broadcast, write an internal preparation brief for the next broadcast rather than pretending there is a live show today.
- If policy.operation_mode is monday_catchup, separate weekend accumulation from Monday-open items and prefer facts that still matter at Monday 07:20 KST.
- For Monday catch-up, avoid treating every weekend headline equally; keep only items that can become a broadcast lead, market context, or useful backup.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def extract_output_text(raw: dict) -> str:
    if raw.get("output_text"):
        return str(raw["output_text"]).strip()
    return "".join(
        content.get("text", "")
        for item in raw.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    ).strip()


def call_openai(prompt: str, token: str, model: str, timeout: int) -> tuple[dict, str | None]:
    payload = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_editorial_brief",
                "strict": True,
                "schema": EDITORIAL_SCHEMA,
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
    text = extract_output_text(raw)
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(text), raw.get("id")


def load_fixture_response(path: Path) -> tuple[dict, str | None]:
    text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    if isinstance(payload, dict) and (payload.get("output_text") or payload.get("output")):
        extracted = extract_output_text(payload)
        if not extracted:
            raise RuntimeError("fixture response did not contain output_text")
        return json.loads(extracted), payload.get("id")
    if isinstance(payload, dict):
        return payload, payload.get("id")
    raise ValueError("fixture must be a JSON object")


def star_label(stars: int) -> str:
    return {3: "강추", 2: "추천", 1: "보조"}.get(stars, "보조")


def fallback_brief(target_date: str, reason: str) -> dict:
    radar = load_json(PROCESSED_DIR / target_date / "market-radar.json")
    candidates = {item.get("id"): item for item in radar.get("candidates") or []}
    storylines = []
    for story in (radar.get("storylines") or [])[:3]:
        evidence = []
        for item_id in story.get("selected_item_ids") or []:
            item = candidates.get(item_id)
            if not item:
                continue
            evidence.append({"item_id": item_id, "title": title_of(item), "reason": "기존 점수 기반 후보에서 선택된 자료입니다."})
        stars = int(story.get("recommendation_stars") or 2)
        storylines.append(
            {
                "title": compact_text(story.get("title"), 80),
                "recommendation_stars": max(1, min(3, stars)),
                "rating_reason": story.get("recommendation_label") or star_label(stars),
                "hook": compact_text(story.get("one_liner") or story.get("title"), 180),
                "why_now": compact_text(story.get("why_selected") or "오늘 수집 자료에서 상대적으로 강하게 잡힌 방송 후보입니다.", 220),
                "core_argument": compact_text(story.get("angle") or story.get("one_liner") or "", 220),
                "evidence_to_use": evidence[:4],
                "evidence_to_drop": [],
                "slide_order": [title for title in (story.get("slide_order") or []) if title][:3]
                or [item["title"] for item in evidence[:3]],
                "talk_track": compact_text(story.get("talk_track") or story.get("one_liner") or story.get("angle"), 260),
                "counterpoint": "API 편집 단계가 실패해 기존 규칙 기반 후보를 사용했습니다. 방송 전 사람이 강약을 확인해야 합니다.",
            }
        )
    return {
        "ok": True,
        "fallback": True,
        "fallback_reason": reason,
        "target_date": target_date,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "model": None,
        "daily_thesis": compact_text((storylines[0]["hook"] if storylines else "") or "오늘 시장의 핵심 질문을 선별합니다.", 140),
        "editorial_summary": "OpenAI 편집장 단계가 실패해 기존 market-radar 스토리라인을 사용했습니다.",
        "storylines": storylines,
    }


def validate_brief(brief: dict, input_payload: dict) -> list[str]:
    errors = []
    if not brief.get("daily_thesis"):
        errors.append("missing daily_thesis")
    if not brief.get("editorial_summary"):
        errors.append("missing editorial_summary")
    stories = brief.get("storylines")
    if not isinstance(stories, list) or len(stories) < 3:
        errors.append("storylines must contain at least 3 items")
        return errors
    known_ids = {item["id"] for item in input_payload.get("candidates") or []}
    titles = []
    for index, story in enumerate(stories, start=1):
        title = compact_text(story.get("title"))
        if not title:
            errors.append(f"storyline {index} missing title")
        titles.append(title)
        stars = story.get("recommendation_stars")
        if not isinstance(stars, int) or stars < 1 or stars > 3:
            errors.append(f"storyline {index} invalid recommendation_stars")
        for key in ["hook", "why_now", "talk_track"]:
            if not compact_text(story.get(key)):
                errors.append(f"storyline {index} missing {key}")
        evidence = story.get("evidence_to_use")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"storyline {index} missing evidence_to_use")
        for item in evidence or []:
            if item.get("item_id") not in known_ids:
                errors.append(f"storyline {index} unknown evidence item_id: {item.get('item_id')}")
    duplicates = {title for title in titles if titles.count(title) > 1 and title}
    if duplicates:
        errors.append(f"duplicate storyline titles: {', '.join(sorted(duplicates))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-candidates", type=int, default=28)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--response-fixture", type=Path, help="Read a saved OpenAI response or brief JSON instead of calling the API.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    model = args.model or env.get("AUTOPARK_EDITORIAL_MODEL") or env.get("AUTOPARK_OPENAI_MODEL") or DEFAULT_MODEL
    input_payload = build_input_payload(args.date, args.max_candidates)
    output_path = PROCESSED_DIR / args.date / "editorial-brief.json"

    if args.dry_run:
        preview = {
            "ok": True,
            "status": "dry-run",
            "target_date": args.date,
            "model": model,
            "output": str(output_path),
            "candidate_count": len(input_payload.get("candidates") or []),
            "prompt_payload": input_payload,
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0

    try:
        if args.response_fixture:
            brief, response_id = load_fixture_response(args.response_fixture)
        else:
            token = env.get("OPENAI_API_KEY")
            if not token:
                raise RuntimeError("missing_openai_api_key")
            brief, response_id = call_openai(build_prompt(input_payload), token, model, args.timeout)
        errors = validate_brief(brief, input_payload)
        if errors:
            raise ValueError("; ".join(errors))
        brief = {
            "ok": True,
            "fallback": False,
            "target_date": args.date,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": "fixture" if args.response_fixture else model,
            "raw_response_id": response_id,
            **brief,
        }
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        brief = fallback_brief(args.date, f"{type(exc).__name__}: {exc}")

    write_json(output_path, brief)
    print(
        json.dumps(
            {
                "ok": True,
                "fallback": bool(brief.get("fallback")),
                "output": str(output_path),
                "model": brief.get("model"),
                "storyline_count": len(brief.get("storylines") or []),
                "fallback_reason": brief.get("fallback_reason"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
