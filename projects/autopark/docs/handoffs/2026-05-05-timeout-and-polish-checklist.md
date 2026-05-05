# Autopark 0505 Notion Polish and LLM Timeout Checklist

## Current 0505 Baseline

- Full run: `2026-05-05T07:38:54+09:00` to `2026-05-05T07:55:58+09:00`
- Notion page: `26.05.05`
- Quality gate: `pass`
- Datawrapper publish/export: ok after `.env` BOM handling fix
- Known capture warnings: Finviz, CNN Fear & Greed, CME browser capture, X timeline
- Current scheduler owner: Windows Task Scheduler at 05:00; Docker publisher is stopped to avoid duplicate publish

## Visual / Notion Polish Checklist

- [ ] Check whether top host quote feels like a real two-line morning thesis.
  - Current desired form: one blockquote, no forced sentence splitting.
  - Code owner: `build_live_notion_dashboard.py`, dashboard microcopy input/output.

- [ ] Check storyline titles for repetition across days.
  - The 0505 editorial output is `fallback=false`, but first attempt timed out and compact retry produced the result.
  - Treat compact retry as "usable but lower-context" until the normal path is stable.

- [ ] Check storyline slide lines for `(1)` media focus numbers.
  - They should match `## 2. 미디어 포커스` labels exactly.
  - If media title fallback is generic, storyline labels will also look generic.

- [ ] Check `## 1. 시장은 지금` image quality.
  - Finviz/CNN browser captures may fail or produce stale images; current policy allows publishing without blocking.
  - Next fix should distinguish "fresh success", "stale fallback", and "blank/failed omitted" in review logs.

- [ ] Check chart timestamp wording.
  - Yahoo/CoinGecko charts should use last valid data timestamp in KST.
  - Datawrapper subtitle and Notion `기준:` should match.

- [ ] Check FedWatch and economic calendar placement.
  - `FedWatch` should have one metadata block and two images.
  - `오늘의 경제지표` should be directly after FedWatch, with US table first and global table second.

- [ ] Check media focus title quality.
  - Current renderer prefers `micro_title`, but if evidence microcopy falls back, titles can become generic.
  - Target: Korean-first, around 20 characters, materially distinct.

- [ ] Check media focus content quality.
  - Current target: `**주요 내용**` with 1-3 natural bullets.
  - Avoid English headline dumps and avoid "자료입니다" phrasing.

- [ ] Check media focus candidate diversity.
  - Current top 40 can over-repeat oil/AI/earnings because scoring is still coarse.
  - Add source/topic caps after LLM stability work if the page feels repetitive.

- [ ] Check `## 3. 실적/특징주`.
  - Current public surface intentionally shows only `실적 캘린더`.
  - Do not re-enable ticker drilldown until feature-stock capture is reliable.

## LLM Timeout Checklist

### 1. Measure Without Aggressive Timeouts

- [ ] Add a `--no-api-timeout` or very large timeout option for isolated test scripts.
  - Do not use this in the 05:00 production path yet.
  - Target scripts:
    - `build_market_preflight_agenda.py`
    - `build_evidence_microcopy.py`
    - `build_market_focus_brief.py`
    - `build_editorial_brief.py`

- [ ] Log wall-clock latency for every OpenAI request.
  - Include request id when available.
  - Include prompt chars, estimated tokens, output tokens if available, candidate/item count, model, timeout seconds.

- [ ] Run one controlled 0505 replay with no timeout for each LLM stage separately.
  - Preflight agenda: was timeout at 120s.
  - Evidence microcopy: attempted 2 requests, 200 items, all fallback.
  - Editorial full attempt: 16 candidates, about 42k chars / 10.5k estimated prompt tokens, timeout at 120s.

- [ ] Record whether the request eventually succeeds, fails with gateway/server error, or hangs beyond a practical limit.
  - This separates "too slow but valid" from "request shape is bad" from "network/API instability".

### 2. Evidence Microcopy Alternatives

- [ ] Test smaller grouped request sizes.
  - Current effective run: 200 items, 2 requests, all fallback.
  - Try group sizes: `10`, `20`, `30`, `40`.
  - Measure success rate, latency, fallback count, and total elapsed.

- [ ] Test fewer fields per item.
  - Send only `item_id`, `source_label`, `title/headline`, `published_at`, `source_type`, and trimmed summary/snippet.
  - Exclude verbose source text unless the source is high-value.

- [ ] Test JSON schema strictness.
  - Compare strict schema vs simpler JSON object schema.
  - Watch whether strict output is increasing latency or causing retries.

- [ ] Add partial-save behavior.
  - If group 1 succeeds and group 2 times out, keep group 1 output and fallback only group 2.
  - Persist a per-group request log.

- [ ] Add resume mode.
  - Re-run only failed item groups instead of regenerating all 200.

### 3. Editorial Alternatives

- [ ] Reduce first-attempt editorial input before changing the final Notion format.
  - Current first attempt: 338 total candidates, 16 sent, 42k chars, 10.5k estimated tokens, 120s timeout.
  - Retry path: 4 candidates, 7.5k chars, 1.9k estimated tokens, succeeded in 47s.

- [ ] Test intermediate candidate counts.
  - Candidate counts: `6`, `8`, `10`, `12`.
  - Goal: keep enough context to avoid repetitive storylines, but finish under 90 seconds.

- [ ] Split editorial into two steps if needed.
  - Step A: choose/cluster storyline candidates from compact evidence summaries.
  - Step B: write public-facing storyline copy from only selected materials.
  - Renderer still owns final structure/order constraints.

- [ ] Preserve market focus signal.
  - The retry path currently drops market focus context.
  - Compact retry should include at least market focus titles, why_it_matters, and selected evidence ids.

### 4. Preflight Alternatives

- [ ] Isolate whether preflight timeout is caused by web search.
  - Run with web on and web off using same date.
  - Compare latency and agenda quality.

- [ ] Add a shorter web-search budget.
  - If web search exceeds threshold, keep local headline river collection as the primary source rather than blocking.

- [ ] Make preflight non-critical in public path.
  - It should guide collection and briefing, but not create public claims without local evidence.

### 5. Production Safety Rules

- [ ] Keep 05:00 publish path bounded.
  - No unbounded timeout in morning automation.
  - Use fallback, partial-save, and retry instead.

- [ ] Publish policy can remain `always` during observation period.
  - Quality findings should be visible in review, not block the morning page.

- [ ] Add a post-run LLM summary table.
  - Stage, model, request count, elapsed, timeout/retry/fallback, prompt tokens, item/candidate count.

- [ ] Add alert-level classification.
  - `green`: normal LLM path
  - `yellow`: partial fallback or compact retry
  - `red`: deterministic-only due API failure

## Suggested Test Order For Today

1. Add request timing / no-timeout instrumentation without changing publish format.
2. Run evidence microcopy only with group sizes `10`, `20`, `30`.
3. Run editorial only with candidate counts `6`, `8`, `10`, `12`.
4. Compare elapsed time and output quality from saved JSONs.
5. Patch production defaults based on the best latency/quality tradeoff.
6. Re-run `build_live_notion_dashboard.py --date 2026-05-05` and quality gate.
7. Republish Notion only after the LLM path is measurably better.
