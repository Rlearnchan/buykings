# Market Focus Brief Backlog

## Smoke validation scope

The current synthetic smoke validates the OpenAI API contract, not editorial quality.

- It verifies the Responses API model ID, strict JSON schema output, response parsing, and optional `web_search` tool/include contract.
- It does not send the real 2026-05-03 local collected source packet to OpenAI.
- Editorial quality is validated through the fixture contract, local 0503 dashboard render, quality gates, and future operating-day retrospectives.

## Hybrid API architecture

The v0 hybrid flow separates discovery timing from editorial authority.

- Call 1: `Pre-flight Market Agenda` runs before collection. It asks what to look for, may use web search for discovery, and returns agenda items plus collection targets.
- Collection, capture, and `market-radar` still produce the local `item_id`/`evidence_id` ledger.
- Call 2: `Market Focus Brief` runs after `market-radar`. It receives only the sanitized local packet plus the preflight agenda as a hypothesis.
- `Market Focus Brief` is the evidence-linked judgment layer. It can promote only stories tied to local `evidence_id`/`source_id`; web-only or preflight-only discoveries remain `source_gap`.
- `Editorial Brief` uses Market Focus as an upstream ranking prior, not as standalone evidence.
- The dashboard shows only compact status labels and host-ready order at the top. Preflight raw agenda, long judgment rationale, URLs, source roles, and evidence roles live in `2. 미디어 포커스` or audit/debug.

Fallback rules:

- Pre-flight failure must not block fixed collection; the pipeline continues with fixed charts/news/X capture.
- Market Focus failure must keep the market-radar fallback and mark `Market Focus Brief: fallback 사용` in the top host view.
- `fallback_code` should distinguish `model_not_available`, `auth_failed`, `rate_limited`, and generic API/parser errors where possible.

## v0.1 sanitized local packet

Design a sanitized packet mode for production OpenAI calls so the model can rank local evidence without receiving raw source material.

Packet rules:

- Exclude raw URLs, screenshot paths, long original headlines, full article bodies, and full X/social post text.
- Include only `source_id`, compact `title`, `source_role`, `evidence_role`, compact summary, chart title/takeaway, and asset status.
- Keep X/social entries as sentiment/context only, with no full post text.
- Preserve enough stable IDs for `evidence_id` linking and retrospective comparison.
- Keep source gaps explicit when the sanitized packet is insufficient to promote a focus publicly.

Acceptance notes:

- `build_market_focus_brief.py` can build either the current local packet or the sanitized packet through an explicit flag/env policy.
- Quality gates continue to fail public promotion when a lead lacks local `evidence_id` or a related `source_gap`.
- The Notion renderer still keeps original titles, URLs, captures, and source-role details in `2. 미디어 포커스` or audit/debug only.

## v1 price_confirmation structure

`price_confirmation` is a compact string in v0. Promote it to a structured object once the renderer and quality gate need machine-readable price validation.

Target shape:

```json
{
  "needed": ["US10Y", "DXY", "WTI"],
  "confirmed": ["US10Y up", "DXY firm"],
  "missing": ["sector close confirmation"],
  "interpretation": "Rates and dollar confirm the constraint; oil is a watchpoint until WTI follows."
}
```

Acceptance notes:

- `needed`: assets or indicators required before a focus can become lead.
- `confirmed`: observed price/rate/sector reactions already present in local evidence.
- `missing`: checks that should remain in `missing_assets` or `source_gaps`.
- `interpretation`: host-readable conclusion that still treats charts as market reaction, not standalone causality.
