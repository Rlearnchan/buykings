#!/usr/bin/env python3
"""Caption collected visual assets with an OpenAI vision model."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
DEFAULT_ENV = REPO_ROOT / ".env"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RUNTIME_NOTION_DIR = PROJECT_ROOT / "runtime" / "notion"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4.1"


IMAGE_INTEL_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "visual_title": {"type": "string"},
        "chart_type": {"type": "string"},
        "plain_english_caption_ko": {"type": "string"},
        "main_claim_ko": {"type": "string"},
        "key_numbers": {
            "type": "array",
            "items": {"type": "string"},
        },
        "market_context_ko": {"type": "string"},
        "broadcast_hook_ko": {"type": "string"},
        "related_assets": {
            "type": "array",
            "items": {"type": "string"},
        },
        "storyline_tags": {
            "type": "array",
            "items": {"type": "string"},
        },
        "follow_up_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "caveats": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence": {"type": "number"},
        "needs_manual_review": {"type": "boolean"},
    },
    "required": [
        "visual_title",
        "chart_type",
        "plain_english_caption_ko",
        "main_claim_ko",
        "key_numbers",
        "market_context_ko",
        "broadcast_hook_ko",
        "related_assets",
        "storyline_tags",
        "follow_up_questions",
        "caveats",
        "confidence",
        "needs_manual_review",
    ],
}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def image_data_url(path: Path) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def gather_assets(target_date: str, only_needs_visual_reasoning: bool = False) -> list[dict]:
    processed = PROCESSED_DIR / target_date
    assets: list[dict] = []

    if only_needs_visual_reasoning:
        visual_cards = load_json(processed / "visual-cards.json")
        for card in visual_cards.get("cards", []):
            local_path = card.get("local_path")
            if not local_path or not card.get("needs_visual_reasoning"):
                continue
            assets.append(
                {
                    "asset_id": card.get("id") or f"{card.get('candidate_id')}-{len(assets) + 1}",
                    "kind": "visual_card_needs_reasoning",
                    "source_id": card.get("source_id"),
                    "source_name": card.get("source_name"),
                    "source_url": card.get("url"),
                    "headline": card.get("title"),
                    "published_at": card.get("published_at"),
                    "context_text": "\n".join(
                        part
                        for part in [
                            card.get("description") or "",
                            "\n".join(card.get("page_paragraphs") or []),
                        ]
                        if part
                    ),
                    "image_alt": card.get("image_alt") or "",
                    "image_url": card.get("image_url") or "",
                    "local_path": local_path,
                    "reasoning_reasons": card.get("visual_reasoning_reasons") or [],
                }
            )
        return assets

    for filename in ["today-misc-batch-b-candidates.json"]:
        payload = load_json(processed / filename)
        for candidate in payload.get("candidates", []):
            for image in candidate.get("image_refs", []):
                local_path = image.get("local_path")
                if not local_path:
                    continue
                assets.append(
                    {
                        "asset_id": f"{candidate.get('id')}-{len(assets) + 1}",
                        "kind": "research_chart_image",
                        "source_id": candidate.get("source_id"),
                        "source_name": candidate.get("source_name"),
                        "source_url": candidate.get("url"),
                        "headline": candidate.get("headline"),
                        "published_at": candidate.get("published_at"),
                        "context_text": candidate.get("summary") or candidate.get("headline") or "",
                        "image_alt": image.get("alt") or "",
                        "image_url": image.get("url") or image.get("src") or "",
                        "local_path": local_path,
                    }
                )

    x_payload = load_json(processed / "x-timeline-posts.json")
    for post in x_payload.get("posts", []):
        for image in post.get("image_refs", []):
            local_path = image.get("local_path")
            if not local_path:
                continue
            assets.append(
                {
                    "asset_id": f"{post.get('source_id')}-{len(assets) + 1}",
                    "kind": "x_post_image",
                    "source_id": post.get("source_id"),
                    "source_name": post.get("source_name"),
                    "source_url": post.get("url") or post.get("account_url"),
                    "headline": (post.get("text") or "").splitlines()[0][:120],
                    "published_at": post.get("created_at") or post.get("created_at_inferred"),
                    "context_text": post.get("text") or "",
                    "image_alt": image.get("alt") or "",
                    "image_url": image.get("src") or image.get("url") or "",
                    "local_path": local_path,
                }
            )

    return assets


def build_prompt(asset: dict) -> str:
    return f"""You are assisting a Korean morning-market-broadcast researcher.

Analyze the attached market/research visual. Use the surrounding page/post context, but do not invent precise numbers that are not legible. If a number is hard to read, say it needs manual review.

Return Korean explanations for the broadcast fields. Focus on:
- What the chart/image is trying to say.
- Why a market viewer should care today.
- How a host could use it in a 30-60 second storyline.
- What must be checked before putting it on air.

Source: {asset.get('source_name') or '-'}
URL: {asset.get('source_url') or '-'}
Headline/title: {asset.get('headline') or '-'}
Image alt text: {asset.get('image_alt') or '-'}
Published/time: {asset.get('published_at') or '-'}
Surrounding text:
{asset.get('context_text') or '-'}
"""


def call_openai(asset: dict, token: str, model: str, timeout: int) -> dict:
    image_path = resolve_path(asset["local_path"])
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": build_prompt(asset)},
                    {"type": "input_image", "image_url": image_data_url(image_path)},
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "visual_market_caption",
                "strict": True,
                "schema": IMAGE_INTEL_SCHEMA,
            }
        },
    }
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))

    text_parts: list[str] = []
    for item in raw.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text_parts.append(content.get("text", ""))
    parsed_text = "".join(text_parts).strip()
    if not parsed_text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return {"raw_response_id": raw.get("id"), "caption": json.loads(parsed_text)}


def render_review(results: list[dict], target_date: str) -> str:
    lines = [
        f"# 이미지 해석 후보 {target_date}",
        "",
        "OpenAI vision captioning PoC 결과입니다. 숫자 판독은 방송 전 수동 확인이 필요합니다.",
        "",
    ]
    for index, result in enumerate(results, start=1):
        asset = result["asset"]
        caption = result.get("caption") or {}
        lines.extend(
            [
                f"## 후보 {index}. {caption.get('visual_title') or asset.get('headline') or asset.get('asset_id')}",
                "",
                f"- 출처: [{asset.get('source_name')}]({asset.get('source_url')})",
                f"- 이미지: `{asset.get('local_path')}`",
                f"- 상태: {result.get('status')}",
                f"- 한 줄 해석: {caption.get('main_claim_ko') or '-'}",
                f"- 방송 훅: {caption.get('broadcast_hook_ko') or '-'}",
                f"- 관련 자산: {', '.join(caption.get('related_assets') or []) or '-'}",
                f"- 주의점: {'; '.join(caption.get('caveats') or []) or '-'}",
                "",
            ]
        )
    if not results:
        lines.append("- 후보 없음")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="2026-04-28")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=os.environ.get("AUTOPARK_OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--only-needs-visual-reasoning",
        action="store_true",
        help="Caption only the image cards flagged by build_visual_cards.py as needing model interpretation",
    )
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    token = env.get("OPENAI_API_KEY")
    assets = gather_assets(args.date, args.only_needs_visual_reasoning)[: args.limit]
    results = []

    for asset in assets:
        image_path = resolve_path(asset["local_path"])
        base = {"asset": asset, "image_exists": image_path.exists()}
        if args.dry_run or not token:
            status = "dry-run" if args.dry_run else "skipped_missing_openai_api_key"
            results.append({**base, "status": status, "caption": None})
            continue
        try:
            started = time.time()
            parsed = call_openai(asset, token, args.model, args.timeout)
            results.append(
                {
                    **base,
                    "status": "ok",
                    "elapsed_seconds": round(time.time() - started, 2),
                    **parsed,
                }
            )
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
            detail = exc.read().decode("utf-8", errors="replace") if isinstance(exc, urllib.error.HTTPError) else str(exc)
            results.append({**base, "status": "error", "error": detail, "caption": None})

    output_dir = PROCESSED_DIR / args.date
    notion_dir = RUNTIME_NOTION_DIR / args.date
    output_dir.mkdir(parents=True, exist_ok=True)
    notion_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "target_date": args.date,
        "model": args.model,
        "asset_count": len(assets),
        "results": results,
    }
    (output_dir / "image-intel.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (notion_dir / "image-intel-review.md").write_text(render_review(results, args.date), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
