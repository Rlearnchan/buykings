#!/usr/bin/env python3
"""Build the upstream Pre-flight Market Agenda for Autopark."""

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
RUNTIME_NOTION_DIR = RUNTIME_DIR / "notion"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "market_preflight_agenda.md"
DEFAULT_ENV = REPO_ROOT / ".env"
OPENAI_API = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_REASONING_EFFORT = "medium"

TARGET_TYPES = {"chart", "news_search", "x_search", "official_source", "market_reaction", "capture"}
EXPECTED_USES = {"lead_candidate", "supporting_candidate", "watch_only", "drop"}


class OpenAIAPIError(RuntimeError):
    def __init__(self, label: str, status: int | None, api_code: str, message: str, body: str = "") -> None:
        self.label = label
        self.status = status
        self.api_code = api_code
        self.message = message
        self.body = body
        super().__init__(f"{label}: status={status}; api_code={api_code}; message={message}")


COLLECTION_TARGET_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["target_type", "query_or_asset", "preferred_sources", "reason"],
    "properties": {
        "target_type": {"type": "string", "enum": sorted(TARGET_TYPES)},
        "query_or_asset": {"type": "string"},
        "preferred_sources": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
}

AGENDA_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "rank",
        "agenda_id",
        "market_question",
        "why_to_check",
        "expected_broadcast_use",
        "collection_targets",
        "must_verify_with_local_evidence",
        "public_safe",
    ],
    "properties": {
        "rank": {"type": "integer", "minimum": 1, "maximum": 12},
        "agenda_id": {"type": "string"},
        "market_question": {"type": "string"},
        "why_to_check": {"type": "string"},
        "expected_broadcast_use": {"type": "string", "enum": sorted(EXPECTED_USES)},
        "collection_targets": {"type": "array", "minItems": 1, "maxItems": 12, "items": COLLECTION_TARGET_SCHEMA},
        "must_verify_with_local_evidence": {"type": "boolean"},
        "public_safe": {"type": "boolean"},
    },
}

COLLECTION_PRIORITIES_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["fixed_charts", "targeted_news_queries", "targeted_x_queries", "official_or_primary_sources"],
    "properties": {
        "fixed_charts": {"type": "array", "items": {"type": "string"}},
        "targeted_news_queries": {"type": "array", "items": {"type": "string"}},
        "targeted_x_queries": {"type": "array", "items": {"type": "string"}},
        "official_or_primary_sources": {"type": "array", "items": {"type": "string"}},
    },
}

DO_NOT_USE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["reason", "rule"],
    "properties": {"reason": {"type": "string"}, "rule": {"type": "string"}},
}

PREFLIGHT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "date",
        "preflight_summary",
        "agenda_items",
        "collection_priorities",
        "do_not_use_publicly",
        "source_gaps_to_watch",
    ],
    "properties": {
        "date": {"type": "string"},
        "preflight_summary": {"type": "string"},
        "agenda_items": {"type": "array", "minItems": 1, "maxItems": 8, "items": AGENDA_ITEM_SCHEMA},
        "collection_priorities": COLLECTION_PRIORITIES_SCHEMA,
        "do_not_use_publicly": {"type": "array", "items": DO_NOT_USE_SCHEMA},
        "source_gaps_to_watch": {"type": "array", "items": {"type": "string"}},
    },
}


def compact_text(value: object, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def slug_id(value: object, fallback: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return compact_text(text or fallback, 80).replace("…", "")


def unique_strings(values: list[object], limit: int = 12, item_limit: int = 120) -> list[str]:
    rows: list[str] = []
    for value in values:
        text = compact_text(value, item_limit)
        if text and text not in rows:
            rows.append(text)
        if len(rows) >= limit:
            break
    return rows


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


def load_optional_json(path: Path) -> dict:
    if not path or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_json(payload: dict) -> None:
    try:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except UnicodeEncodeError:
        print(json.dumps(payload, ensure_ascii=True, indent=2))


def truthy(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def recent_retrospective_hints(limit: int = 4) -> list[str]:
    payload = load_optional_json(PROJECT_ROOT / "config" / "retrospective_learning.json")
    hints: list[str] = []
    for value in payload.get("prompt_updates") or []:
        hints.append(compact_text(value, 160))
    for value in payload.get("actions") or []:
        hints.append(compact_text(value, 160))
    return unique_strings(hints, limit=limit, item_limit=160)


def build_input_payload(target_date: str, synthetic_smoke: bool = False) -> dict:
    return {
        "date": target_date,
        "broadcast_context": {
            "channel": "위폴/바이킹스",
            "start_time_kst": "07:20",
            "audience": "한국 개인투자자",
            "preferred_style": "compact, market-first, PPT-friendly",
            "synthetic_smoke": bool(synthetic_smoke),
        },
        "fixed_watchlist": {
            "markets": ["S&P500", "Nasdaq", "Dow", "Russell2000"],
            "macro": ["US10Y", "DXY", "USD/KRW", "WTI", "Brent", "Bitcoin"],
            "policy": ["Fed", "FOMC", "inflation", "jobs"],
            "earnings": ["big tech", "semiconductors", "AI infrastructure"],
        },
        "recent_retrospective_hints": [] if synthetic_smoke else recent_retrospective_hints(),
        "policy": {
            "public_evidence": False,
            "local_raw_packet": False,
            "web_search_is_discovery_only": True,
            "must_verify_later_with_local_evidence": True,
        },
    }


def prompt_template() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8").strip()
    return "You are a pre-flight market agenda editor. Return JSON only."


def build_prompt(payload: dict, with_web: bool = True) -> str:
    web_note = (
        "Web search is enabled. Use it only for discovery hints and collection planning; it is not public evidence."
        if with_web
        else "Web search is disabled. Build a collection agenda only from the fixed watchlist and retrospective hints."
    )
    return f"""{prompt_template()}

Runtime mode:
{web_note}

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def classify_openai_error(status: int | None, api_code: str, message: str) -> str:
    text = f"{api_code} {message}".lower()
    if api_code in {"model_not_available", "model_not_found"}:
        return "model_not_available"
    if "model" in text and (
        "not available" in text
        or "does not exist" in text
        or "do not have access" in text
        or "not have access" in text
        or "not found" in text
    ):
        return "model_not_available"
    if status == 401:
        return "auth_failed"
    if status == 429:
        return "rate_limited"
    if status and status >= 500:
        return "openai_server_error"
    return "preflight_openai_unavailable"


def openai_http_error(exc: urllib.error.HTTPError) -> OpenAIAPIError:
    body = exc.read().decode("utf-8", errors="replace")
    api_code = f"http_{exc.code}"
    message = exc.reason or body[:240]
    try:
        payload = json.loads(body)
        error = payload.get("error") if isinstance(payload, dict) else {}
        if isinstance(error, dict):
            api_code = str(error.get("code") or error.get("type") or api_code)
            message = str(error.get("message") or message)
    except json.JSONDecodeError:
        pass
    label = classify_openai_error(exc.code, api_code, message)
    return OpenAIAPIError(label, exc.code, api_code, compact_text(message, 500), compact_text(body, 1000))


def extract_output_text(raw: dict) -> str:
    if raw.get("output_text"):
        return str(raw["output_text"]).strip()
    return "".join(
        content.get("text", "")
        for item in raw.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    ).strip()


def extract_web_sources(raw: dict) -> list[dict]:
    sources: list[dict] = []
    for item in raw.get("output") or []:
        action = item.get("action") or {}
        for source in action.get("sources") or []:
            if isinstance(source, dict):
                sources.append(
                    {
                        "title": compact_text(source.get("title") or "", 160),
                        "source": compact_text(source.get("source") or "", 80),
                    }
                )
    return sources


def call_openai(prompt: str, token: str, model: str, timeout: int, with_web: bool, reasoning_effort: str) -> tuple[dict, str | None, list[dict]]:
    payload: dict = {
        "model": model,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "autopark_market_preflight_agenda",
                "strict": True,
                "schema": PREFLIGHT_SCHEMA,
            }
        },
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    if with_web:
        payload["tools"] = [{"type": "web_search"}]
        payload["tool_choice"] = "auto"
        payload["include"] = ["web_search_call.action.sources"]
    request = urllib.request.Request(
        OPENAI_API,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise openai_http_error(exc) from exc
    text = extract_output_text(raw)
    if not text:
        raise RuntimeError("OpenAI response did not contain output_text")
    return json.loads(text), raw.get("id"), extract_web_sources(raw)


def load_fixture_response(path: Path) -> tuple[dict, str | None, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("agenda"), dict):
        return payload["agenda"], payload.get("raw_response_id") or payload.get("id"), payload.get("web_sources") or []
    if isinstance(payload, dict) and (payload.get("output_text") or payload.get("output")):
        extracted = extract_output_text(payload)
        if not extracted:
            raise RuntimeError("fixture response did not contain output_text")
        return json.loads(extracted), payload.get("id"), extract_web_sources(payload)
    if isinstance(payload, dict):
        return payload, payload.get("id"), payload.get("web_sources") or []
    raise ValueError("fixture must be a JSON object")


def normalize_target(item: dict) -> dict:
    target_type = str(item.get("target_type") or "news_search")
    if target_type not in TARGET_TYPES:
        target_type = "news_search"
    return {
        "target_type": target_type,
        "query_or_asset": compact_text(item.get("query_or_asset") or item.get("query") or item.get("asset") or "", 160),
        "preferred_sources": unique_strings(item.get("preferred_sources") or [], limit=8, item_limit=80),
        "reason": compact_text(item.get("reason") or "", 180),
    }


def normalize_agenda_item(item: dict, index: int) -> dict:
    expected = str(item.get("expected_broadcast_use") or "watch_only")
    if expected not in EXPECTED_USES:
        expected = "watch_only"
    targets = [normalize_target(row) for row in item.get("collection_targets") or [] if isinstance(row, dict)]
    if not targets:
        targets = [
            {
                "target_type": "news_search",
                "query_or_asset": compact_text(item.get("market_question") or "market agenda verification", 160),
                "preferred_sources": ["Reuters", "Bloomberg", "CNBC"],
                "reason": "agenda item needs local fact/data evidence",
            }
        ]
    return {
        "rank": index,
        "agenda_id": slug_id(item.get("agenda_id") or item.get("market_question"), f"agenda_{index}"),
        "market_question": compact_text(item.get("market_question") or "", 220),
        "why_to_check": compact_text(item.get("why_to_check") or "", 260),
        "expected_broadcast_use": expected,
        "collection_targets": targets[:12],
        "must_verify_with_local_evidence": True,
        "public_safe": False,
    }


def normalize_agenda(payload: dict, target_date: str) -> dict:
    items = [
        normalize_agenda_item(item, index)
        for index, item in enumerate(payload.get("agenda_items") or [], start=1)
        if isinstance(item, dict)
    ]
    items = items[:8]
    priorities = payload.get("collection_priorities") if isinstance(payload.get("collection_priorities"), dict) else {}
    do_not_use = [
        {
            "reason": compact_text(item.get("reason") or "", 180),
            "rule": compact_text(item.get("rule") or "", 220),
        }
        for item in payload.get("do_not_use_publicly") or []
        if isinstance(item, dict)
    ]
    if not do_not_use:
        do_not_use = [
            {
                "reason": "Pre-flight is a discovery layer without evidence_id.",
                "rule": "Public dashboard must use only evidence-linked Market Focus results.",
            }
        ]
    return {
        "date": compact_text(payload.get("date") or target_date, 20),
        "preflight_summary": compact_text(payload.get("preflight_summary"), 100),
        "agenda_items": items,
        "collection_priorities": {
            "fixed_charts": unique_strings(priorities.get("fixed_charts") or [], limit=16, item_limit=80),
            "targeted_news_queries": unique_strings(priorities.get("targeted_news_queries") or [], limit=12, item_limit=140),
            "targeted_x_queries": unique_strings(priorities.get("targeted_x_queries") or [], limit=12, item_limit=140),
            "official_or_primary_sources": unique_strings(priorities.get("official_or_primary_sources") or [], limit=12, item_limit=80),
        },
        "do_not_use_publicly": do_not_use,
        "source_gaps_to_watch": unique_strings(payload.get("source_gaps_to_watch") or [], limit=12, item_limit=180),
    }


def validate_agenda(agenda: dict) -> list[str]:
    errors: list[str] = []
    for key in PREFLIGHT_SCHEMA["required"]:
        if key not in agenda:
            errors.append(f"missing {key}")
    if not compact_text(agenda.get("preflight_summary")):
        errors.append("missing preflight_summary")
    items = agenda.get("agenda_items")
    if not isinstance(items, list) or not items:
        errors.append("agenda_items must contain at least one item")
        return errors
    for index, item in enumerate(items, start=1):
        for key in AGENDA_ITEM_SCHEMA["required"]:
            if key not in item:
                errors.append(f"agenda {index} missing {key}")
        if item.get("public_safe") is not False:
            errors.append(f"agenda {index} public_safe must be false")
        targets = item.get("collection_targets")
        if not isinstance(targets, list) or not targets:
            errors.append(f"agenda {index} collection_targets must contain at least one item")
    return errors


def fallback_agenda(target_date: str, reason: str, model: str | None = None, with_web: bool = False, fallback_code: str = "preflight_openai_unavailable") -> dict:
    agenda = normalize_agenda(
        {
            "date": target_date,
            "preflight_summary": "금리·달러, 유가, AI 인프라를 먼저 확인한다.",
            "agenda_items": [
                {
                    "rank": 1,
                    "agenda_id": "agenda_rates_dollar",
                    "market_question": "실적 호조가 금리·달러 부담을 이길 수 있는가?",
                    "why_to_check": "금리와 달러가 위험자산 상단을 제한할 수 있다.",
                    "expected_broadcast_use": "lead_candidate",
                    "collection_targets": [
                        {"target_type": "chart", "query_or_asset": "US10Y", "preferred_sources": ["market-data"], "reason": "금리 반응 확인"},
                        {"target_type": "chart", "query_or_asset": "DXY", "preferred_sources": ["market-data"], "reason": "달러 부담 확인"},
                        {"target_type": "news_search", "query_or_asset": "Fed inflation Reuters market reaction", "preferred_sources": ["Reuters", "Bloomberg"], "reason": "fact anchor 확보"},
                    ],
                },
                {
                    "rank": 2,
                    "agenda_id": "agenda_oil_risk",
                    "market_question": "지정학 뉴스가 유가와 에너지주 반응으로 확인되는가?",
                    "why_to_check": "유가가 따라오지 않으면 리스크 체크용 보조 꼭지에 가깝다.",
                    "expected_broadcast_use": "supporting_candidate",
                    "collection_targets": [
                        {"target_type": "chart", "query_or_asset": "WTI Brent", "preferred_sources": ["market-data"], "reason": "유가 반응 확인"},
                        {"target_type": "news_search", "query_or_asset": "oil Iran WTI Brent market reaction", "preferred_sources": ["Reuters", "CNBC"], "reason": "fact anchor 확보"},
                    ],
                },
            ],
            "collection_priorities": {
                "fixed_charts": ["major indices", "heatmap", "US10Y", "WTI", "DXY", "USD/KRW", "Bitcoin"],
                "targeted_news_queries": ["Fed inflation Reuters market reaction", "oil Iran WTI Brent market reaction"],
                "targeted_x_queries": ["US10Y DXY Nasdaq reaction", "WTI Brent Iran risk"],
                "official_or_primary_sources": ["Fed", "Reuters", "CME FedWatch"],
            },
            "do_not_use_publicly": [],
            "source_gaps_to_watch": ["Pre-flight fallback agenda must be verified by local evidence before public use."],
        },
        target_date,
    )
    return {
        "ok": True,
        "fallback": True,
        "fallback_code": fallback_code,
        "fallback_reason": reason,
        "target_date": target_date,
        "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "model": model,
        "with_web": bool(with_web),
        **agenda,
    }


def render_markdown(agenda: dict) -> str:
    status = "fallback 사용" if agenda.get("fallback") else "정상"
    lines = [
        "# Market Pre-flight Agenda",
        "",
        f"- target_date: `{agenda.get('target_date') or agenda.get('date')}`",
        f"- generated_at: `{agenda.get('created_at') or datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')}`",
        f"- model: `{agenda.get('model') or 'none'}`",
        f"- with_web: `{bool(agenda.get('with_web'))}`",
        f"- status: `{status}`",
    ]
    if agenda.get("fallback"):
        lines.append(f"- fallback_code: `{agenda.get('fallback_code') or 'unknown'}`")
        lines.append(f"- fallback_reason: {compact_text(agenda.get('fallback_reason') or '', 220)}")
    lines.extend(["", "## Summary", "", agenda.get("preflight_summary") or "-", "", "## Agenda Items", ""])
    for item in agenda.get("agenda_items") or []:
        lines.extend(
            [
                f"### {item.get('rank')}. {item.get('agenda_id')}",
                "",
                f"- market_question: {item.get('market_question')}",
                f"- why_to_check: {item.get('why_to_check')}",
                f"- expected_broadcast_use: `{item.get('expected_broadcast_use')}`",
                f"- public_safe: `{bool(item.get('public_safe'))}`",
                "- collection_targets:",
            ]
        )
        for target in item.get("collection_targets") or []:
            sources = ", ".join(target.get("preferred_sources") or []) or "-"
            lines.append(f"  - `{target.get('target_type')}` {target.get('query_or_asset')} / sources: {sources} / {target.get('reason')}")
        lines.append("")
    priorities = agenda.get("collection_priorities") or {}
    lines.extend(["## Collection Priorities", ""])
    for key in ["fixed_charts", "targeted_news_queries", "targeted_x_queries", "official_or_primary_sources"]:
        values = priorities.get(key) or []
        lines.append(f"- {key}: " + (", ".join(values) if values else "-"))
    lines.extend(["", "## Do Not Use Publicly", ""])
    for item in agenda.get("do_not_use_publicly") or []:
        lines.append(f"- {item.get('reason')} / {item.get('rule')}")
    lines.extend(["", "## Source Gaps To Watch", ""])
    for item in agenda.get("source_gaps_to_watch") or []:
        lines.append(f"- {item}")
    if not agenda.get("source_gaps_to_watch"):
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def resolve_model(args_model: str | None, env: dict[str, str]) -> str:
    return args_model or env.get("AUTOPARK_PREFLIGHT_MODEL") or env.get("AUTOPARK_OPENAI_MODEL") or DEFAULT_MODEL


def resolve_with_web(args: argparse.Namespace, env: dict[str, str]) -> bool:
    if args.no_web:
        return False
    if args.with_web:
        return True
    return truthy(env.get("AUTOPARK_PREFLIGHT_WITH_WEB"), default=True)


def write_raw_response(target_date: str, model: str, response_id: str | None, agenda: dict, source: str, web_sources: list[dict]) -> Path:
    path = RUNTIME_DIR / "openai-responses" / f"{target_date}-market-preflight-raw.json"
    write_json(
        path,
        {
            "source": source,
            "model": model,
            "raw_response_id": response_id,
            "web_sources": web_sources,
            "agenda": agenda,
        },
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--model", default=None)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--with-web", action="store_true")
    parser.add_argument("--no-web", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--response-fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--prompt-output", type=Path)
    parser.add_argument("--synthetic-smoke", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = {**load_env(args.env.resolve()), **os.environ}
    model = resolve_model(args.model, env)
    with_web = resolve_with_web(args, env)
    reasoning_effort = args.reasoning_effort or env.get("AUTOPARK_PREFLIGHT_REASONING_EFFORT") or DEFAULT_REASONING_EFFORT
    input_payload = build_input_payload(args.date, synthetic_smoke=args.synthetic_smoke)
    output_path = args.output or (PROCESSED_DIR / args.date / "market-preflight-agenda.json")
    markdown_path = args.markdown_output or (RUNTIME_NOTION_DIR / f"{args.date}-market-preflight-agenda.md")
    prompt = build_prompt(input_payload, with_web=with_web)
    fixture_meta = load_optional_json(args.response_fixture) if args.response_fixture else {}
    fixture_model = fixture_meta.get("model") if isinstance(fixture_meta, dict) else None

    if args.prompt_output:
        write_json(
            args.prompt_output,
            {
                "ok": True,
                "target_date": args.date,
                "model": model,
                "with_web": with_web,
                "input_payload": input_payload,
                "prompt": prompt,
            },
        )

    if args.dry_run:
        print_json(
            {
                "ok": True,
                "status": "dry-run",
                "target_date": args.date,
                "model": model,
                "with_web": with_web,
                "synthetic_smoke": bool(args.synthetic_smoke),
                "output": str(output_path),
                "markdown_output": str(markdown_path),
            }
        )
        return 0

    response_id = None
    raw_response_path = ""
    web_sources: list[dict] = []
    try:
        if args.response_fixture:
            agenda, response_id, web_sources = load_fixture_response(args.response_fixture)
            response_source = "fixture"
        else:
            token = env.get("OPENAI_API_KEY")
            if not token:
                raise RuntimeError("missing_openai_api_key")
            agenda, response_id, web_sources = call_openai(prompt, token, model, args.timeout, with_web, reasoning_effort)
            response_source = "openai_responses_api_with_web" if with_web else "openai_responses_api"
        raw_response_path = (
            str(args.response_fixture.resolve())
            if args.response_fixture and args.response_fixture.resolve().parent == (RUNTIME_DIR / "openai-responses").resolve()
            else str(write_raw_response(args.date, model, response_id, agenda, response_source, web_sources))
        )
        agenda = normalize_agenda(agenda, args.date)
        errors = validate_agenda(agenda)
        if errors:
            raise ValueError("; ".join(errors))
        agenda = {
            "ok": True,
            "fallback": False,
            "target_date": args.date,
            "created_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
            "model": fixture_model or ("fixture" if args.response_fixture else model),
            "with_web": bool(with_web),
            "raw_response_id": response_id,
            "raw_response_path": raw_response_path,
            "web_sources": web_sources,
            **agenda,
        }
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        fallback_code = exc.label if isinstance(exc, OpenAIAPIError) else "preflight_openai_unavailable"
        agenda = fallback_agenda(
            args.date,
            f"{type(exc).__name__}: {exc}",
            model=model,
            with_web=with_web,
            fallback_code=fallback_code,
        )

    write_json(output_path, agenda)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(agenda), encoding="utf-8")
    print_json(
        {
            "ok": True,
            "fallback": bool(agenda.get("fallback")),
            "output": str(output_path),
            "markdown_output": str(markdown_path),
            "model": agenda.get("model"),
            "with_web": bool(agenda.get("with_web")),
            "synthetic_smoke": bool(args.synthetic_smoke),
            "agenda_count": len(agenda.get("agenda_items") or []),
            "fallback_code": agenda.get("fallback_code"),
            "fallback_reason": agenda.get("fallback_reason"),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
