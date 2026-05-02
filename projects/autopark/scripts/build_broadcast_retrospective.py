#!/usr/bin/env python3
"""Compare an Autopark dashboard with the actual Wepoll broadcast transcript."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"


RETROSPECTIVE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "overall_assessment",
        "hit_rate_estimate",
        "used_storylines",
        "missed_broadcast_topics",
        "unused_dashboard_items",
        "format_issues",
        "source_feedback",
        "prompt_updates",
        "code_change_suggestions",
        "summary_for_next_brief",
    ],
    "properties": {
        "overall_assessment": {"type": "string"},
        "hit_rate_estimate": {"type": "number", "minimum": 0, "maximum": 1},
        "used_storylines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "status", "evidence", "comment"],
                "properties": {
                    "title": {"type": "string"},
                    "status": {"type": "string"},
                    "evidence": {"type": "string"},
                    "comment": {"type": "string"},
                },
            },
        },
        "missed_broadcast_topics": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["topic", "broadcast_evidence", "suggested_source_or_query"],
                "properties": {
                    "topic": {"type": "string"},
                    "broadcast_evidence": {"type": "string"},
                    "suggested_source_or_query": {"type": "string"},
                },
            },
        },
        "unused_dashboard_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["item", "reason"],
                "properties": {
                    "item": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "format_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["issue", "fix"],
                "properties": {
                    "issue": {"type": "string"},
                    "fix": {"type": "string"},
                },
            },
        },
        "source_feedback": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["source", "verdict", "reason"],
                "properties": {
                    "source": {"type": "string"},
                    "verdict": {"type": "string"},
                    "reason": {"type": "string"},
                },
            },
        },
        "prompt_updates": {"type": "array", "items": {"type": "string"}},
        "code_change_suggestions": {"type": "array", "items": {"type": "string"}},
        "summary_for_next_brief": {"type": "string"},
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
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def display_date_title(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%y.%m.%d")


def compact(value: object, limit: int = 4000) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def read_text(path: Path, limit: int = 40_000) -> str:
    if not path.exists():
        return ""
    return compact(path.read_text(encoding="utf-8", errors="replace"), limit)


def default_notion_path(target_date: str) -> Path:
    return RUNTIME_DIR / "notion" / target_date / f"{display_date_title(target_date)}.md"


def find_timestamp(value: object) -> str | None:
    if isinstance(value, str) and re.search(r"20\d{2}-\d{2}-\d{2}", value):
        return value
    if isinstance(value, dict):
        for key in ["captured_at", "fetched_at", "created_at", "checked_at", "timestamp"]:
            found = find_timestamp(value.get(key))
            if found:
                return found
        for child in value.values():
            found = find_timestamp(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value[:20]:
            found = find_timestamp(child)
            if found:
                return found
    return None


def collection_limitations(target_date: str) -> list[dict]:
    raw_dir = RAW_DIR / target_date
    if not raw_dir.exists():
        return [{"type": "missing_raw_dir", "detail": f"No raw directory for {target_date}"}]

    limitations: list[dict] = []
    target = datetime.fromisoformat(target_date).date()
    for path in sorted(raw_dir.glob("*.json")):
        payload = load_json(path)
        timestamp = find_timestamp(payload)
        source = payload.get("source") or payload.get("name") or path.stem
        status = payload.get("status")
        if status and status not in {"ok", "success", "downloaded"}:
            limitations.append(
                {
                    "type": "source_status",
                    "source": source,
                    "file": path.name,
                    "status": status,
                }
            )
        if not timestamp:
            limitations.append(
                {
                    "type": "missing_capture_timestamp",
                    "source": source,
                    "file": path.name,
                    "detail": "Cannot verify whether this source reflects the target date.",
                }
            )
            continue
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", timestamp)
        if not match:
            continue
        captured_date = datetime.fromisoformat(match.group(1)).date()
        if captured_date != target:
            limitations.append(
                {
                    "type": "stale_or_live_only_capture",
                    "source": source,
                    "file": path.name,
                    "captured_at": timestamp,
                    "target_date": target_date,
                    "detail": "This source appears to be a live/current capture, not a historical replay for the target date.",
                }
            )
    return limitations


def build_input_payload(target_date: str, transcript_path: Path | None, notion_path: Path | None) -> dict:
    day_dir = RUNTIME_DIR / "broadcast" / target_date
    transcript_json = load_json(day_dir / "wepoll-transcript.json")
    if transcript_path is None:
        transcript_path = day_dir / "host-segment.md"
    if notion_path is None:
        notion_path = default_notion_path(target_date)
    processed = PROCESSED_DIR / target_date
    brief = load_json(processed / "editorial-brief.json")
    radar = load_json(processed / "market-radar.json")
    quality = load_json(RUNTIME_DIR / "reviews" / target_date / "dashboard-quality.json")
    return {
        "date": target_date,
        "notion_markdown_path": str(notion_path),
        "transcript_path": str(transcript_path),
        "video": {
            "status": transcript_json.get("status"),
            "video_id": transcript_json.get("video_id"),
            "title": transcript_json.get("title"),
            "video_url": transcript_json.get("video_url"),
            "host_minutes": transcript_json.get("host_minutes"),
        },
        "dashboard_quality": {
            "gate": quality.get("gate"),
            "format_score": quality.get("format_score"),
            "content_score": quality.get("content_score"),
            "findings": quality.get("findings") or [],
        },
        "collection_limitations": collection_limitations(target_date),
        "editorial_brief": {
            "daily_thesis": brief.get("daily_thesis"),
            "editorial_summary": brief.get("editorial_summary"),
            "storylines": [
                {
                    "title": story.get("title"),
                    "stars": story.get("recommendation_stars"),
                    "hook": story.get("hook"),
                    "why_now": story.get("why_now"),
                    "evidence_to_use": story.get("evidence_to_use") or [],
                }
                for story in (brief.get("storylines") or [])
            ],
        },
        "candidate_titles": [
            {
                "id": item.get("id"),
                "title": compact(item.get("title") or item.get("headline") or item.get("summary"), 180),
                "source": item.get("source") or item.get("type") or item.get("publisher") or "",
                "score": item.get("score") or item.get("final_score") or 0,
            }
            for item in (radar.get("candidates") or [])[:40]
        ],
        "notion_markdown_excerpt": read_text(notion_path, 24_000),
        "broadcast_transcript": read_text(transcript_path, 36_000),
    }


def build_prompt(payload: dict) -> str:
    return f"""You are a Korean broadcast post-mortem editor for Autopark.

Compare the morning dashboard with the actual host segment transcript.

Important rules:
- The transcript is an imperfect auto-generated Korean caption. Be conservative.
- Focus only on the first host segment, not guest/interview sections.
- Do not quote long transcript passages. Use short evidence snippets only.
- Judge whether Autopark helped the actual broadcast: hit, partial hit, miss, unused.
- Separate content misses from format/presentation errors.
- If collection_limitations lists stale/live-only captures or missing timestamps, mention them as operational issues and propose a concrete prevention rule.
- Suggest prompt/config/source-weight changes. Do not directly rewrite code.
- Treat the dashboard as pre-broadcast material and the transcript as post-broadcast feedback.
- Keep Korean concise and operational.

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
                "name": "autopark_broadcast_retrospective",
                "strict": True,
                "schema": RETROSPECTIVE_SCHEMA,
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


def keyword_fallback(payload: dict, reason: str) -> dict:
    transcript = str(payload.get("broadcast_transcript") or "").lower()
    used = []
    for story in payload.get("editorial_brief", {}).get("storylines") or []:
        title = str(story.get("title") or "")
        tokens = [token.lower() for token in re.split(r"\W+", title) if len(token) >= 3]
        overlap = sum(1 for token in tokens if token in transcript)
        status = "partial_hit" if overlap else "unknown"
        used.append(
            {
                "title": title,
                "status": status,
                "evidence": "키워드 단순 비교 기반입니다.",
                "comment": "LLM 회고 실패로 정확한 방송 맥락 판단은 보류합니다.",
            }
        )
    return {
        "overall_assessment": f"LLM 회고 생성 실패: {reason}",
        "hit_rate_estimate": 0.0,
        "used_storylines": used,
        "missed_broadcast_topics": [],
        "unused_dashboard_items": [],
        "format_issues": [],
        "source_feedback": [],
        "prompt_updates": ["LLM 회고를 다시 실행하세요."],
        "code_change_suggestions": [],
        "summary_for_next_brief": "방송 회고를 생성하지 못했습니다. 다음 편집장 단계는 기존 자료만 참고해야 합니다.",
    }


def render_markdown(target_date: str, review: dict, payload: dict) -> str:
    lines = [
        f"# Broadcast Retrospective - {target_date}",
        "",
        f"- 생성 시각: `{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%y.%m.%d %H:%M')} (KST)`",
        f"- 영상: {payload.get('video', {}).get('title') or '-'}",
        f"- transcript: `{payload.get('transcript_path')}`",
        f"- dashboard: `{payload.get('notion_markdown_path')}`",
        f"- hit rate estimate: `{review.get('hit_rate_estimate')}`",
        "",
    ]
    limitations = payload.get("collection_limitations") or []
    if limitations:
        lines.extend(["## 수집 한계", ""])
        for item in limitations[:20]:
            source = item.get("source") or item.get("file") or item.get("type") or "-"
            detail = item.get("detail") or item.get("status") or "-"
            captured_at = f" captured_at={item.get('captured_at')}" if item.get("captured_at") else ""
            lines.append(f"- `{item.get('type')}` {source}: {detail}{captured_at}")
        if len(limitations) > 20:
            lines.append(f"- ...and {len(limitations) - 20} more")
        lines.append("")
    lines.extend(
        [
            "## 총평",
            "",
            review.get("overall_assessment") or "-",
            "",
            "## 스토리라인 적중",
            "",
        ]
    )
    for item in review.get("used_storylines") or []:
        lines.extend(
            [
                f"### {item.get('title') or '-'}",
                "",
                f"- 상태: `{item.get('status') or '-'}`",
                f"- 근거: {item.get('evidence') or '-'}",
                f"- 코멘트: {item.get('comment') or '-'}",
                "",
            ]
        )
    if not review.get("used_storylines"):
        lines.append("- 없음")

    lines.extend(["", "## 놓친 방송 주제", ""])
    for item in review.get("missed_broadcast_topics") or []:
        lines.append(f"- {item.get('topic')}: {item.get('broadcast_evidence')} / 보강: {item.get('suggested_source_or_query')}")
    if not review.get("missed_broadcast_topics"):
        lines.append("- 없음")

    lines.extend(["", "## 포맷 이슈", ""])
    for item in review.get("format_issues") or []:
        lines.append(f"- {item.get('issue')}: {item.get('fix')}")
    if not review.get("format_issues"):
        lines.append("- 없음")

    lines.extend(["", "## 소스 피드백", ""])
    for item in review.get("source_feedback") or []:
        lines.append(f"- {item.get('source')} `{item.get('verdict')}`: {item.get('reason')}")
    if not review.get("source_feedback"):
        lines.append("- 없음")

    lines.extend(["", "## 다음 프롬프트 메모", ""])
    for item in review.get("prompt_updates") or []:
        lines.append(f"- {item}")
    if not review.get("prompt_updates"):
        lines.append("- 없음")

    lines.extend(["", "## 코드/운영 개선 후보", ""])
    for item in review.get("code_change_suggestions") or []:
        lines.append(f"- {item}")
    if not review.get("code_change_suggestions"):
        lines.append("- 없음")

    lines.extend(["", "## 다음 브리프에 넘길 요약", "", review.get("summary_for_next_brief") or "-"])
    return "\n".join(lines).rstrip() + "\n"


def render_feedback_md(target_date: str, review: dict) -> str:
    lines = [
        f"# Broadcast Feedback Summary - {target_date}",
        "",
        review.get("summary_for_next_brief") or review.get("overall_assessment") or "-",
        "",
        "## Prompt Updates",
        "",
    ]
    lines.extend(f"- {item}" for item in (review.get("prompt_updates") or [])[:8])
    if not review.get("prompt_updates"):
        lines.append("- 없음")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--notion", type=Path)
    parser.add_argument("--env", type=Path, default=REPO_ROOT / ".env")
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = build_input_payload(args.date, args.transcript, args.notion)
    review_dir = RUNTIME_DIR / "reviews" / args.date
    review_md = review_dir / "broadcast-retrospective.md"
    review_json = review_dir / "broadcast-retrospective.json"
    feedback_md = RUNTIME_DIR / "broadcast" / args.date / "retrospective-feedback.md"
    env = {**load_env(args.env.resolve()), **os.environ}
    model = args.model or env.get("AUTOPARK_RETROSPECTIVE_MODEL") or env.get("AUTOPARK_OPENAI_MODEL") or DEFAULT_MODEL

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": "dry-run",
                    "date": args.date,
                    "model": model,
                    "review_markdown": str(review_md),
                    "review_json": str(review_json),
                    "feedback_markdown": str(feedback_md),
                    "has_transcript": bool(payload.get("broadcast_transcript")),
                    "has_dashboard": bool(payload.get("notion_markdown_excerpt")),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    try:
        if not payload.get("broadcast_transcript"):
            raise RuntimeError("missing_broadcast_transcript")
        if not payload.get("notion_markdown_excerpt"):
            raise RuntimeError("missing_notion_markdown")
        token = env.get("OPENAI_API_KEY")
        if not token:
            raise RuntimeError("missing_openai_api_key")
        review, response_id = call_openai(build_prompt(payload), token, model, args.timeout)
        fallback = False
        fallback_reason = None
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        review = keyword_fallback(payload, f"{type(exc).__name__}: {exc}")
        response_id = None
        fallback = True
        fallback_reason = f"{type(exc).__name__}: {exc}"

    output = {
        "ok": True,
        "fallback": fallback,
        "fallback_reason": fallback_reason,
        "date": args.date,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "model": None if fallback else model,
        "raw_response_id": response_id,
        "input": {
            "transcript_path": payload.get("transcript_path"),
            "notion_markdown_path": payload.get("notion_markdown_path"),
            "video": payload.get("video"),
            "collection_limitations": payload.get("collection_limitations") or [],
        },
        "review": review,
    }
    write_json(review_json, output)
    write_text(review_md, render_markdown(args.date, review, payload))
    write_text(feedback_md, render_feedback_md(args.date, review))
    print(
        json.dumps(
            {
                "ok": True,
                "fallback": fallback,
                "fallback_reason": fallback_reason,
                "review_markdown": str(review_md),
                "review_json": str(review_json),
                "feedback_markdown": str(feedback_md),
                "hit_rate_estimate": review.get("hit_rate_estimate"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
