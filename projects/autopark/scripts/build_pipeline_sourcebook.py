from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
REPO_ROOT = PROJECT_DIR.parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
RUNTIME_DIR = PROJECT_DIR / "runtime"
DOCS_DIR = PROJECT_DIR / "docs" / "sourcebooks"
EXPORTS_DIR = PROJECT_DIR / "exports" / "current"
CIRCLED_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

HYGIENE_PATTERNS = {
    "AKIA": re.compile(r"AKIA[0-9A-Z]{16}"),
    "OPENAI_API_KEY": re.compile(r"OPENAI_API_KEY|sk-[A-Za-z0-9_-]{20,}"),
    "X-Amz-Signature": re.compile(r"X-Amz-Signature=", re.I),
    "AWSAccessKeyId": re.compile(r"AWSAccessKeyId=", re.I),
    "SessionToken": re.compile(r"SessionToken|X-Amz-Security-Token", re.I),
    "Set-Cookie": re.compile(r"Set-Cookie:", re.I),
    "raw_html_body": re.compile(r"<html\b|<!doctype html|<body\b|</body>", re.I),
    "full_x_text_dump": re.compile(r"(?s)(?:full_x_text|x_full_text|raw_text)\s*[:=]"),
    "signed_image_url": re.compile(r"https?://[^\s)]+(?:X-Amz-|Signature=|AWSAccessKeyId=|Key-Pair-Id=|Policy=)[^\s)]*", re.I),
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compact(value: Any, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def repo_path(path: str | Path) -> str:
    resolved = Path(path)
    try:
        return str(resolved.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        parts = list(resolved.parts)
        if "projects" in parts:
            return str(Path(*parts[parts.index("projects") :]))
        return resolved.name


def safe_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if re.search(r"X-Amz-|Signature=|AWSAccessKeyId=|Key-Pair-Id=|Policy=|token=|sig=", text, flags=re.I):
        match = re.match(r"https?://([^/]+)", text)
        return f"https://{match.group(1) if match else 'url'}/[redacted]"
    return text


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(compact(cell, 180).replace("|", "/") for cell in row) + " |")
    return "\n".join(output)


def bullet_list(items: list[Any]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- none"


def source_result_rows(payload: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for row in payload.get("source_results") or []:
        if isinstance(row, dict):
            rows.append(
                [
                    row.get("name") or row.get("source") or row.get("url"),
                    row.get("status") or row.get("ok"),
                    row.get("count") or len(row.get("items") or []),
                    row.get("error") or row.get("fallback_code") or "",
                ]
            )
        else:
            rows.append([row, "", "", ""])
    return rows


def candidate_rows(items: list[Any], max_rows: int = 10) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for index, item in enumerate(items[:max_rows], start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                index,
                item.get("title") or item.get("headline") or item.get("summary") or item.get("focus") or item.get("id") or item.get("ticker"),
                item.get("source") or item.get("source_name") or item.get("type") or item.get("ticker"),
                " / ".join(str(item.get(key) or "") for key in ["source_tier", "source_authority", "source_role", "evidence_role"] if item.get(key)),
                safe_url(item.get("url") or item.get("source_url")),
            ]
        )
    return rows


def raw_response_summary(path_value: Any) -> list[str]:
    if not path_value:
        return ["- raw response: none"]
    path = Path(str(path_value))
    rows = [f"- raw response path: `{repo_path(path)}`"]
    if not path.exists():
        rows.append("- raw response file: not readable from current path")
        return rows
    payload = read_json(path)
    rows.extend(
        [
            f"- raw response size: `{path.stat().st_size:,}` bytes",
            f"- raw_response_id: `{payload.get('raw_response_id') or payload.get('id') or ''}`",
            f"- model: `{payload.get('model') or ''}`",
            f"- top keys: `{', '.join(sorted(payload.keys()))}`",
        ]
    )
    for key in ["agenda", "brief"]:
        if isinstance(payload.get(key), dict):
            rows.append(f"- `{key}` keys: `{', '.join(sorted(payload[key].keys())[:50])}`")
    return rows


def prompt_safety_rows(prompt_check_path: Path) -> list[str]:
    if not prompt_check_path.exists():
        return ["- prompt check file: missing"]
    payload = read_json(prompt_check_path)
    blob = json.dumps(payload, ensure_ascii=False)
    body_keys = ["body", "html", "full_text", "raw_text", "article_body", "x_full_text"]
    values = {
        "model": payload.get("model"),
        "with_web": payload.get("with_web"),
        "prompt_chars": len(payload.get("prompt") or ""),
        "http_url_count": blob.count("http://") + blob.count("https://"),
        "signed_url_hits": len(re.findall(r"X-Amz-|Signature=|AWSAccessKeyId=|Key-Pair-Id=|Policy=", blob, flags=re.I)),
        "local_path_hits": len(re.findall(r"[A-Za-z]:\\|/Users/|/home/", blob)),
        "body_like_key_hits": sum(1 for key in body_keys if f'"{key}"' in blob),
        "ev_alias_count": len(re.findall(r"ev_[A-Za-z0-9_-]+", blob)),
        "input_payload_keys": ", ".join(sorted((payload.get("input_payload") or {}).keys())),
    }
    return [f"- {key}: `{value}`" for key, value in values.items()]


def parse_card_blocks(section_text: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    content_bullets = 0
    in_content = False
    for line in section_text.splitlines():
        if line.startswith("### "):
            if current:
                current["has_content"] = content_bullets > 0
                cards.append(current)
            current = {
                "label": line[4:].strip(),
                "source": "",
                "has_content": False,
                "image_count": 0,
            }
            content_bullets = 0
            in_content = False
            continue
        if not current:
            continue
        if line.startswith("- 출처:"):
            current["source"] = line.split(":", 1)[1].strip()
        elif line.startswith("!["):
            current["image_count"] += 1
        elif line.strip() == "**주요 내용**" or line.startswith("- 내용:"):
            in_content = True
        elif in_content and re.match(r"^\s*-+\s+", line):
            content_bullets += 1
    if current:
        current["has_content"] = content_bullets > 0
        cards.append(current)
    return cards


def extract_between(markdown: str, start: str, end: str | None = None) -> str:
    start_index = markdown.find(start)
    if start_index < 0:
        return ""
    start_index += len(start)
    if not end:
        return markdown[start_index:]
    end_index = markdown.find(end, start_index)
    return markdown[start_index:] if end_index < 0 else markdown[start_index:end_index]


def renderer_summary(markdown: str) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    story_labels = re.findall(r"^- `([^`]+)`$", markdown, flags=re.M)
    story_labels.extend(re.findall(r"`([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s+[^`]+)`", markdown))
    story_labels = list(dict.fromkeys(story_labels))
    market_body = extract_between(markdown, "## 1. 시장은 지금", "## 2. 미디어 포커스")
    media_body = extract_between(markdown, "## 2. 미디어 포커스")
    forbidden = [
        "source_role",
        "evidence_role",
        "item_id",
        "evidence_id",
        "asset_id",
        "MF-",
        "# PPT 제작 큐",
        "자료 수집 상세",
        "Audit",
        "Debug",
    ]
    return story_labels, parse_card_blocks(market_body), parse_card_blocks(media_body), {token: markdown.count(token) for token in forbidden}


def trace_blob(value: Any) -> str:
    return compact(json.dumps(value, ensure_ascii=False), 2000).lower()


def preflight_downgrade_trace(preflight: dict[str, Any], focus: dict[str, Any], radar: dict[str, Any]) -> list[list[Any]]:
    focus_items = [item for item in focus.get("what_market_is_watching") or [] if isinstance(item, dict)]
    public_blob = trace_blob([item for item in focus_items if item.get("broadcast_use") in {"lead", "supporting_story", "talk_only"}])
    downgrade_ledgers = {
        "source_gap": focus.get("source_gaps") or [],
        "false_lead": focus.get("false_leads") or [],
        "missing_assets": focus.get("missing_assets") or [],
        "drop": [item for item in focus_items if item.get("broadcast_use") == "drop"],
    }
    downgrade_blobs = {name: trace_blob(payload) for name, payload in downgrade_ledgers.items()}
    local_blob = trace_blob(radar.get("candidates") or [])
    rows: list[list[Any]] = []
    for item in preflight.get("agenda_items") or []:
        if not isinstance(item, dict):
            continue
        agenda_id = compact(item.get("agenda_id") or f"rank-{item.get('rank')}", 80)
        question = compact(item.get("market_question"), 140)
        tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9가-힣/.-]{4,}", f"{agenda_id} {question}")]
        public_hit = any(token in public_blob for token in tokens[:12])
        downgrade_hits = [name for name, blob in downgrade_blobs.items() if any(token in blob for token in tokens[:12])]
        local_hit = any(token in local_blob for token in tokens[:12])
        if public_hit:
            status = "public_focus"
            trace = "Market Focus public item"
        elif downgrade_hits:
            status = "downgraded"
            trace = "/".join(downgrade_hits)
        elif local_hit:
            status = "local_evidence_only"
            trace = "collected locally but not promoted"
        else:
            status = "source_gap"
            trace = "source_gap (not confirmed by local evidence)"
        rows.append([item.get("rank"), agenda_id, status, trace, question])
    return rows


def build_sourcebook(target_date: str, output: Path) -> Path:
    processed = PROCESSED_DIR / target_date
    runtime_date = RUNTIME_DIR / "notion" / target_date / f"{target_date[2:4]}.{target_date[5:7]}.{target_date[8:10]}.md"
    prompt_check = RUNTIME_DIR / "notion" / f"{target_date}-market-focus-prompt-check.json"
    fallback_prompt_check = REPO_ROOT / "projects" / "autopark" / "runtime" / "notion" / f"{target_date}-market-focus-prompt-check.json"
    if not prompt_check.exists() and fallback_prompt_check.exists():
        prompt_check = fallback_prompt_check

    preflight = read_json(processed / "market-preflight-agenda.json")
    focus = read_json(processed / "market-focus-brief.json")
    editorial = read_json(processed / "editorial-brief.json")
    radar = read_json(processed / "market-radar.json")
    headline_river = read_json(processed / "headline-river.json")
    analysis_river = read_json(processed / "analysis-river.json")
    batch_a = read_json(processed / "today-misc-batch-a-candidates.json")
    batch_b = read_json(processed / "today-misc-batch-b-candidates.json")
    x_posts = read_json(processed / "x-timeline-posts.json")
    visual = read_json(processed / "visual-cards.json")
    finviz = read_json(processed / "finviz-feature-stocks.json")
    earnings = read_json(processed / "earnings-ticker-drilldown.json")
    economic = read_json(processed / "economic-calendar.json")
    evidence_microcopy = read_json(processed / "evidence-microcopy.json")
    microcopy = read_json(processed / "dashboard-microcopy.json")
    quality = read_json(RUNTIME_DIR / "reviews" / target_date / "dashboard-quality.json")
    dashboard_markdown = runtime_date.read_text(encoding="utf-8") if runtime_date.exists() else ""
    story_labels, market_cards, media_cards, forbidden_counts = renderer_summary(dashboard_markdown)

    lines: list[str] = [
        f"# {target_date[2:4]}.{target_date[5:7]}.{target_date[8:10]} Autopark Pipeline Sourcebook",
        "",
        f"- Generated at: `{datetime.now().strftime('%y.%m.%d %H:%M')}`",
        "- Scope: end-to-end sourcebook for the compact dashboard pipeline: collection, API reasoning, filtering, renderer decisions, and quality gate.",
        "- Hygiene: credentials, browser/session data, signed URLs, raw HTML, full article bodies, and full X text are not included.",
        "- Long source material is represented as title/source/role/URL/summary only.",
        "",
        "## 0. Artifact Inventory",
    ]
    for path in sorted(processed.glob("*.json")):
        lines.append(f"- `{repo_path(path)}` ({path.stat().st_size:,} bytes)")
    if runtime_date.exists():
        lines.append(f"- `{repo_path(runtime_date)}` ({runtime_date.stat().st_size:,} bytes)")

    lines.extend(
        [
            "",
            "## 1. Pipeline Order",
            bullet_list(
                [
                    "Pre-flight Market Agenda: web-enabled discovery agenda and collection targets",
                    "News batch A/B: collect candidate news and record source failures",
                    "Headline River: keep broad Finviz/Yahoo/BizToc headline baseline and preflight-linked Yahoo expansions",
                    "Analysis River: normalize specialist X/chart/earnings sources as context, separate from news distribution",
                    "X/earnings timeline: collect X timeline posts and earnings calendar context",
                    "Visual cards and captures: collect Finviz, market charts, FedWatch, Fear & Greed, and chart exports",
                    "Market Radar: merge local candidates into a candidate DB with internal source/evidence roles",
                    "Source Policy: annotate evidence with source tier, authority, allowed use, and auth profile hints",
                    "Evidence Microcopy: grouped candidate summaries after market-radar; no ranking/ordering authority",
                    "Market Focus Brief: call OpenAI with sanitized local packet; no web_search; promote only local-evidence-backed focus items",
                    "Editorial Brief: turn focus/radar into broadcast storylines and material queue",
                    "Fixed compact renderer: LLM supplies values; renderer owns section structure/order/exposed fields",
                    "Quality gate: validate compact host area, collection structure, forbidden tokens, and media label matching",
                ]
            ),
            "",
            "## 2. Pre-flight Market Agenda",
            f"- Input: `target_date={preflight.get('target_date') or preflight.get('date')}`, `with_web={preflight.get('with_web')}`",
            f"- Model: `{preflight.get('model')}`, fallback: `{preflight.get('fallback')}`",
            f"- Public-use guard: `{compact(preflight.get('do_not_use_publicly'), 500)}`",
            f"- agenda_items: `{len(preflight.get('agenda_items') or [])}`",
            f"- collection_priorities: `{len(preflight.get('collection_priorities') or [])}`",
            *raw_response_summary(preflight.get("raw_response_path")),
        ]
    )
    preflight_rows = []
    for item in preflight.get("agenda_items") or []:
        targets = "; ".join(
            f"{target.get('target_type')}:{compact(target.get('query_or_asset') or target.get('query'), 50)}"
            for target in item.get("collection_targets") or []
        )
        preflight_rows.append([item.get("rank"), item.get("agenda_id"), item.get("market_question"), targets, item.get("why_to_check")])
    lines.extend(["", markdown_table(["rank", "agenda_id", "market_question", "collection_targets", "why_to_check"], preflight_rows), ""])
    lines.extend(
        [
            "### preflight_downgrade_trace",
            "- Internal trace only; not rendered in publish Markdown.",
            markdown_table(["rank", "agenda_id", "status", "trace_destination", "market_question"], preflight_downgrade_trace(preflight, focus, radar)),
            "",
        ]
    )

    lines.append("## 3. News / X / Earnings Collection")
    lines.extend(
        [
            "### Headline River",
            f"- item_count: `{headline_river.get('item_count') or len(headline_river.get('items') or [])}`",
            f"- baseline_source_ids: `{', '.join(headline_river.get('baseline_source_ids') or [])}`",
            f"- support_source_ids: `{', '.join(headline_river.get('support_source_ids') or [])}`",
            f"- agenda_expansions: `{len(headline_river.get('agenda_expansions') or [])}`",
            "- Role: broad headline/anomaly layer. It expands later reasoning but does not select public storylines by itself.",
            markdown_table(
                ["source", "status", "role", "count"],
                [
                    [
                        stat.get("source_label") or stat.get("source_id"),
                        stat.get("status"),
                        stat.get("source_role"),
                        stat.get("item_count"),
                    ]
                    for stat in (headline_river.get("source_stats") or [])[:20]
                    if isinstance(stat, dict)
                ],
            ),
            "Agenda-linked expansions",
            markdown_table(
                ["rank", "agenda_id", "tickers"],
                [
                    [item.get("rank"), item.get("agenda_id"), ", ".join(item.get("tickers") or [])]
                    for item in (headline_river.get("agenda_expansions") or [])[:8]
                    if isinstance(item, dict)
                ],
            ),
            "BizToc / headline anomaly summary",
            markdown_table(
                ["kind", "top signals"],
                [
                    [
                        "keywords",
                        ", ".join(f"{row.get('keyword')}({row.get('count')})" for row in ((headline_river.get("anomaly_summary") or {}).get("top_keywords") or [])[:12]),
                    ],
                    [
                        "hosts",
                        ", ".join(f"{row.get('host')}({row.get('count')})" for row in ((headline_river.get("anomaly_summary") or {}).get("top_hosts") or [])[:12]),
                    ],
                    [
                        "title_tokens",
                        ", ".join(f"{row.get('token')}({row.get('count')})" for row in ((headline_river.get("anomaly_summary") or {}).get("top_title_tokens") or [])[:12]),
                    ],
                ],
            ),
            markdown_table(
                ["item_id", "source", "role", "title", "agenda_links"],
                [
                    [
                        item.get("item_id"),
                        item.get("source_label"),
                        item.get("source_role"),
                        item.get("title"),
                        ", ".join(item.get("agenda_links") or []),
                    ]
                    for item in (headline_river.get("items") or [])[:25]
                    if isinstance(item, dict)
                ],
            ),
            "",
        ]
    )
    for label, payload, key in [
        ("News batch A", batch_a, "candidates"),
        ("News batch B", batch_b, "candidates"),
        ("X timeline", x_posts, "posts"),
    ]:
        lines.extend(
            [
                f"### {label}",
                f"- captured_at: `{payload.get('captured_at')}`",
                f"- lookback_hours: `{payload.get('lookback_hours')}`",
                f"- require_recent_signal: `{payload.get('require_recent_signal')}`",
                f"- collected_count: `{len(payload.get(key) or [])}`",
            ]
        )
        if source_result_rows(payload):
            lines.extend(["", markdown_table(["source", "status", "count", "error/fallback"], source_result_rows(payload)[:20])])
        lines.extend(["", "Representative candidates", markdown_table(["#", "title/headline", "source", "role", "url"], candidate_rows(payload.get(key) or [])), ""])
    lines.extend(
        [
            "### Analysis River",
            f"- item_count: `{analysis_river.get('item_count') or len(analysis_river.get('items') or [])}`",
            f"- source_count: `{analysis_river.get('source_count') or len(analysis_river.get('analysis_source_ids') or [])}`",
            f"- analysis_source_ids: `{', '.join(analysis_river.get('analysis_source_ids') or [])}`",
            "- Role: specialist commentary, chart context, and earnings reaction. It enriches framing but does not replace local evidence.",
            markdown_table(
                ["role", "count"],
                [
                    [row.get("role"), row.get("count")]
                    for row in (analysis_river.get("role_counts") or [])[:12]
                    if isinstance(row, dict)
                ],
            ),
            markdown_table(
                ["source", "status", "role", "count"],
                [
                    [
                        stat.get("source_label") or stat.get("source_id"),
                        stat.get("status"),
                        stat.get("source_role"),
                        stat.get("item_count"),
                    ]
                    for stat in (analysis_river.get("source_stats") or [])[:24]
                    if isinstance(stat, dict)
                ],
            ),
            markdown_table(
                ["item_id", "source", "role", "title", "content_level"],
                [
                    [
                        item.get("item_id"),
                        item.get("source_label"),
                        item.get("source_role"),
                        item.get("title"),
                        item.get("content_level"),
                    ]
                    for item in (analysis_river.get("items") or [])[:25]
                    if isinstance(item, dict)
                ],
            ),
            "",
        ]
    )
    lines.extend(
        [
            "### Economic / earnings / feature-stock support",
            f"- economic-calendar events: `{len(economic.get('events') or [])}`, countries: `{', '.join(economic.get('countries') or [])}`",
            f"- earnings ticker drilldown tickers: `{earnings.get('ticker_count') or len(earnings.get('tickers') or [])}`",
            f"- finviz feature stocks: `{len(finviz.get('items') or [])}`",
            markdown_table(["#", "title/headline", "source", "role", "url"], candidate_rows(finviz.get("items") or [], 8)),
            "",
        ]
    )

    screenshots = sorted((RUNTIME_DIR / "screenshots" / target_date).glob("*.png")) if (RUNTIME_DIR / "screenshots" / target_date).exists() else []
    exports = sorted(EXPORTS_DIR.glob("*.png")) if EXPORTS_DIR.exists() else []
    lines.extend(
        [
            "## 4. Visual Cards / Captures / Charts",
            f"- visual cards: `{len(visual.get('cards') or [])}`",
            f"- visual stats: `{json.dumps(visual.get('stats') or {}, ensure_ascii=False)}`",
            f"- screenshots: `{len(screenshots)}` under `{repo_path(RUNTIME_DIR / 'screenshots' / target_date)}`",
            f"- chart exports: `{len(exports)}` under `{repo_path(EXPORTS_DIR)}`",
            markdown_table(["kind", "file"], [["screenshot", repo_path(path)] for path in screenshots[:20]] + [["chart", repo_path(path)] for path in exports[:20]]),
            "",
            "## 5. Market Radar Merge / Selection",
            f"- generated_at: `{radar.get('generated_at')}`",
            f"- candidate_count: `{radar.get('candidate_count') or len(radar.get('candidates') or [])}`",
            f"- storylines in radar: `{len(radar.get('storylines') or [])}`",
            "- Internal role/id fields remain available for audit, but are not rendered in publish Markdown.",
            markdown_table(
                ["id", "title", "source", "tier", "authority", "source_role", "evidence_role"],
                [
                    [
                        candidate.get("id") or candidate.get("item_id"),
                        candidate.get("title") or candidate.get("headline"),
                        candidate.get("source") or candidate.get("source_name"),
                        candidate.get("source_tier") or (candidate.get("source_policy") or {}).get("tier"),
                        candidate.get("source_authority") or (candidate.get("source_policy") or {}).get("authority"),
                        candidate.get("source_role"),
                        candidate.get("evidence_role"),
                    ]
                    for candidate in (radar.get("candidates") or [])[:25]
                ],
            ),
            "",
            "## 6. Market Focus Brief API",
            "- Input: market-radar/local candidates + preflight agenda + sanitized local packet",
            f"- Model: `{focus.get('model')}`, fallback: `{focus.get('fallback')}`, with_web: `{focus.get('with_web')}`",
            f"- focus_count: `{len(focus.get('what_market_is_watching') or [])}`",
            f"- source_gap_count: `{len(focus.get('source_gaps') or [])}`",
            f"- raw_response_id: `{focus.get('raw_response_id') or ''}`",
            "### Sanitized prompt check",
            *prompt_safety_rows(prompt_check),
            *raw_response_summary(focus.get("raw_response_path")),
            "",
            markdown_table(
                ["rank", "use", "focus", "evidence_ids", "host sentence"],
                [
                    [
                        item.get("rank"),
                        item.get("broadcast_use"),
                        item.get("focus"),
                        ", ".join(item.get("evidence_ids") or []),
                        item.get("one_sentence_for_host"),
                    ]
                    for item in focus.get("what_market_is_watching") or []
                ],
            ),
        ]
    )
    if focus.get("source_gaps"):
        lines.extend(
            [
                "### Market Focus source gaps",
                bullet_list(
                    [
                        compact(gap.get("issue") or gap.get("reason") or gap, 180) if isinstance(gap, dict) else compact(gap, 180)
                        for gap in focus.get("source_gaps") or []
                    ]
                ),
            ]
        )
    lines.append("")

    lines.extend(
        [
            "## 6.1 Evidence Microcopy",
            f"- enabled: `{evidence_microcopy.get('enabled')}`",
            f"- model: `{evidence_microcopy.get('model') or ''}`",
            f"- source: `{evidence_microcopy.get('source') or ''}`",
            f"- request_count: `{evidence_microcopy.get('request_count') or 0}`",
            f"- item_count: `{evidence_microcopy.get('item_count') or len(evidence_microcopy.get('items') or [])}`",
            f"- source_item_count: `{evidence_microcopy.get('source_item_count') or evidence_microcopy.get('item_count') or len(evidence_microcopy.get('items') or [])}`",
            f"- radar_candidate_count: `{evidence_microcopy.get('radar_candidate_count') or evidence_microcopy.get('candidate_count') or 0}`",
            f"- headline_item_count: `{evidence_microcopy.get('headline_item_count') or 0}`",
            f"- analysis_item_count: `{evidence_microcopy.get('analysis_item_count') or 0}`",
            f"- fallback_count: `{evidence_microcopy.get('fallback_count') or 0}`",
            f"- invalid_output_count: `{evidence_microcopy.get('invalid_output_count') or 0}`",
            f"- estimated_tokens: `{evidence_microcopy.get('estimated_tokens') or 0}`",
            f"- generated fields: `{', '.join(evidence_microcopy.get('generated_fields') or ['title', 'content'])}`",
            "- Input rule: market-radar candidates, headline-river items, and analysis-river items are deduped by URL or source/title before microcopy generation.",
            markdown_table(
                ["item_id", "source", "title", "content"],
                [
                    [
                        item.get("item_id"),
                        item.get("source_label"),
                        item.get("title"),
                        item.get("content") or " / ".join((item.get("summary_bullets") or [])[:1]),
                    ]
                    for item in (evidence_microcopy.get("items") or [])[:30]
                    if isinstance(item, dict)
                ],
            ),
            "",
        ]
    )

    lines.extend(
        [
            "## 7. Editorial Brief API",
            "- Input: Market Focus output + Market Radar candidates + recent briefs/feedback + visual/material candidates",
            f"- Model: `{editorial.get('model')}`, fallback: `{editorial.get('fallback')}`",
            f"- raw_response_id: `{editorial.get('raw_response_id') or ''}`",
            f"- daily_thesis: {compact(editorial.get('daily_thesis'), 180)}",
            f"- market_map_summary: {compact(editorial.get('market_map_summary'), 180)}",
            f"- storyline_count: `{len(editorial.get('storylines') or [])}`",
        ]
    )
    for name, stats in (editorial.get("debug_stats") or {}).items():
        if not isinstance(stats, dict):
            continue
        lines.append(f"### debug_stats.{name}")
        for key in [
            "model",
            "timeout_seconds",
            "request_started_at",
            "request_finished_at",
            "elapsed_seconds",
            "candidate_count_total",
            "candidate_count_sent",
            "market_focus_available",
            "market_focus_focus_count",
            "market_focus_source_gap_count",
            "prompt_chars",
            "estimated_prompt_tokens",
            "max_output_tokens",
            "raw_response_id",
            "fallback_code",
            "fallback_reason",
            "error_code",
            "incomplete_details",
        ]:
            if key in stats:
                lines.append(f"- {key}: `{compact(stats.get(key), 200)}`")
    lines.extend(raw_response_summary(editorial.get("raw_response_path")))
    storyline_rows = []
    for story in editorial.get("storylines") or []:
        labels = ", ".join(
            asset.get("public_material_label") or asset.get("host_facing_material_name") or asset.get("caption") or asset.get("title") or ""
            for asset in story.get("ppt_asset_queue") or []
        )
        evidence = ", ".join(
            item.get("item_id") or item.get("evidence_id") or compact(item.get("title"), 60)
            for item in story.get("evidence_to_use") or []
        )
        storyline_rows.append([story.get("rank"), story.get("recommendation_stars"), story.get("title"), story.get("hook"), evidence, labels])
    lines.extend(
        [
            "",
            markdown_table(["rank", "stars", "title", "hook", "evidence_to_use", "ppt_asset_queue labels"], storyline_rows),
            "",
            "## 8. Fixed Renderer: Visible vs Filtered",
            "- Contract: LLM output supplies values only; renderer owns section names, order, and allowed public fields.",
            "- Host area exposes exactly 3 news bullets, 5 broadcast-order bullets, and 3 storylines.",
            "- Storyline rank >= 4, internal role/id/hash, and raw source metadata are filtered out of the publish host area.",
            "- Collection area exposes only `## 1. 시장은 지금` and `## 2. 미디어 포커스`.",
            "- Market material order is deterministic: index flow -> heatmaps -> rates -> oil -> dollar/FX -> risk assets -> FedWatch.",
            "- Media focus cards follow storyline slide order and receive circled numbers.",
            "### Host slide labels",
            bullet_list([f"`{label}`" for label in story_labels]),
            "### Market-now cards",
            f"- count: `{len(market_cards)}`",
            markdown_table(["label", "source", "has_content", "image_count"], [[c["label"], c["source"], c["has_content"], c["image_count"]] for c in market_cards]),
            "### Media focus cards",
            f"- count: `{len(media_cards)}`",
            markdown_table(["label", "source", "has_content", "image_count"], [[c["label"], c["source"], c["has_content"], c["image_count"]] for c in media_cards]),
            "### Renderer filter check",
        ]
    )
    for token, count in forbidden_counts.items():
        lines.append(f"- {token}: `{count}`")
    lines.extend(
        [
            "",
            "## 8.1 Dashboard Microcopy",
            f"- microcopy_enabled: `{microcopy.get('microcopy_enabled')}`",
            f"- model: `{microcopy.get('model') or ''}`",
            f"- source: `{microcopy.get('source') or ''}`",
            f"- request_count: `{microcopy.get('request_count') or 0}`",
            f"- card_count: `{microcopy.get('card_count') or len(microcopy.get('media_focus_cards') or [])}`",
            f"- fallback_count: `{microcopy.get('fallback_count') or 0}`",
            f"- invalid_output_count: `{microcopy.get('invalid_output_count') or 0}`",
            f"- estimated_tokens: `{microcopy.get('estimated_tokens') or 0}`",
            f"- generated fields: `{', '.join(microcopy.get('generated_fields') or ['quote_lines', 'host_relevance_bullets', 'content_bullets'])}`",
            "### Microcopy storyline fields",
            markdown_table(
                ["storyline_id", "quote_lines", "host_relevance_bullets"],
                [
                    [
                        item.get("storyline_id"),
                        " / ".join(item.get("quote_lines") or []),
                        " / ".join(item.get("host_relevance_bullets") or []),
                    ]
                    for item in microcopy.get("storylines") or []
                ],
            ),
            "### Microcopy media fields",
            markdown_table(
                ["card_key", "content_bullets"],
                [[item.get("card_key"), " / ".join(item.get("content_bullets") or [])] for item in microcopy.get("media_focus_cards") or []],
            ),
        ]
    )
    lines.extend(
        [
            "",
            "## 9. Quality Gate",
            f"- gate: `{quality.get('gate')}`",
            f"- format_score: `{quality.get('format_score')}`",
            f"- content_score: `{quality.get('content_score')}`",
            f"- integrity_score: `{quality.get('integrity_score')}`",
            f"- finding_count: `{quality.get('finding_count')}`",
            "- findings: none"
            if not quality.get("findings")
            else markdown_table(
                ["severity", "category", "title", "detail"],
                [[f.get("severity"), f.get("category"), f.get("title"), f.get("detail")] for f in quality.get("findings")],
            ),
            "",
            "## 10. Reproduction / Trace Files",
            bullet_list(
                [
                    repo_path(processed / "market-preflight-agenda.json"),
                    repo_path(processed / "headline-river.json"),
                    repo_path(processed / "analysis-river.json"),
                    repo_path(processed / "today-misc-batch-a-candidates.json"),
                    repo_path(processed / "today-misc-batch-b-candidates.json"),
                    repo_path(processed / "x-timeline-posts.json"),
                    repo_path(processed / "visual-cards.json"),
                    repo_path(processed / "market-radar.json"),
                    repo_path(processed / "market-focus-brief.json"),
                    repo_path(processed / "editorial-brief.json"),
                    repo_path(runtime_date),
                    repo_path(RUNTIME_DIR / "reviews" / target_date / "dashboard-quality.json"),
                ]
            ),
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def hygiene_findings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings = []
    for name, pattern in HYGIENE_PATTERNS.items():
        if pattern.search(text):
            findings.append(name)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a sanitized Autopark pipeline sourcebook.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--output", help="Output markdown path.")
    parser.add_argument("--hygiene-check", action="store_true", help="Fail if generated sourcebook contains disallowed sensitive/raw payload markers.")
    args = parser.parse_args(argv)

    output = Path(args.output) if args.output else DOCS_DIR / f"{args.date}-pipeline-sourcebook.md"
    path = build_sourcebook(args.date, output)
    findings = hygiene_findings(path) if args.hygiene_check else []
    result = {"ok": not findings, "output": str(path), "hygiene_findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
