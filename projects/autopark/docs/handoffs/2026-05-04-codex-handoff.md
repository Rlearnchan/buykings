# Autopark Codex Handoff - 2026-05-04

## Current Git State

- Branch: `main`
- Latest pushed commit: `df72216f Autopark shrink LLM editorial retry path`
- Remote: `origin/main` is up to date as of the handoff.
- Do not assume the working tree is clean. There are generated/dirty files that should not be staged unless the user explicitly asks.

Recent commits:

- `df72216f` - shrinks editorial LLM first/retry paths and bounds evidence microcopy OpenAI calls.
- `35ceda9c` - softens publish gate and hardens LLM fallbacks.
- `690046fc` - documents Autopark workflow.
- `671829ce` - advances schedule to 05:00 and tunes source scoring.
- `4dfe8962` - rebalances source rivers.
- `531154d2` - uses host Chrome CDP for capture.

## Current Docker State

Autopark is configured to run automatically from Docker:

- Container: `buykings-autopark-publisher`
- Schedule: run `05:00 KST`, retry `05:20 KST`
- Publish policy: `gate`
- CDP: `http://host.docker.internal:9222`
- Browser container/profile path is already in use and healthy as of the handoff.

Other relevant running containers observed:

- `buykings-autopark-browser`
- `buykings-autopark-retrospective`
- `buykings-wepoll-daily-scheduler`
- `syuka-ops-collector-scheduler`
- `syuka-ops-slack-bot`

## What Is Considered MVP Fixed

The user considers the current Autopark output a "1차 완성" MVP.

Keep these fixed unless the user explicitly changes direction:

- Compact Notion dashboard format.
- Top host summary stays compact.
- Storyline quote is one continuous quote block, not sentence-by-sentence fragmented lines.
- `## 1. 시장은 지금` is chart/data oriented and should not have `요약:` or `내용:` prose.
- FedWatch is grouped under one `FedWatch` heading with metadata once.
- Economic calendar is grouped under `오늘의 경제지표` after FedWatch.
- `## 2. 미디어 포커스` is for externally collected media/materials, not internal pipeline stages like Autopark, Market Focus, or Pre-flight.
- Earnings/special stocks belong under `## 3. 실적/특징주`.
- Missing Finviz/CNN capture should publish as absent/blank rather than using stale historical fallback.
- Datawrapper subtitles and Notion 기준 labels use the actual data basis timestamp, e.g. `26.05.01 17:05 KST`, not a separate confirmation timestamp.

## LLM Pipeline Roles

The pipeline uses three higher-level LLM/editor roles, plus microcopy:

- Pre-flight editor: like the morning assignment desk. It scans the day and proposes possible agenda directions.
- Market Focus editor: like the market desk chief. It decides what the market is actually paying attention to from collected evidence.
- Editorial editor: like the front-page editor. It turns market focus and evidence into three broadcast storylines.
- Dashboard microcopy/evidence microcopy: like a copy editor. It writes short public-facing Korean sentences only. It must not decide structure, order, ranking, or material labels.

Important implementation direction:

- Hard tasks use stronger models.
- Simple evidence/card copy uses cheaper grouped model calls where possible.
- If OpenAI fails, deterministic fallback must still produce a publishable dashboard.

## Latest LLM Stability Patch

Commit `df72216f` changed:

- Editorial first request payload is smaller.
- Editorial retry path uses a tiny emergency JSON schema.
- Evidence microcopy produces full item output while sending only the top `AUTOPARK_EVIDENCE_MICROCOPY_LLM_LIMIT` items synchronously to OpenAI.

Observed validation before handoff:

- `python -m unittest discover -s projects/autopark/tests` passed with 97 tests.
- 2026-05-04 dashboard render succeeded.
- Quality gate passed with no blockers.
- Evidence microcopy test produced 200 output items while limiting OpenAI calls to top 40.
- Editorial emergency retry succeeded once with a roughly 7.8k character prompt.
- Later manual OpenAI tests hit `429 Too Many Requests`; do not repeatedly hammer the API unless the user asks.

## Source Strategy Direction

The current agreed source structure is:

Headline river, priority order:

1. Yahoo ticker RSS, expanded from GPT/pre-flight agenda.
2. Legacy X accounts.
3. Biztoc API and Finviz as lower-priority baseline/fill.

Analysis river, no strict hierarchy:

- Kobeissi Letter: macro indicators, market sentiment, chart-based stories.
- Wall St Engine: earnings season, schedules, reaction summaries.
- Liz Ann Sonders: macro direction, labor/inflation/leading indicators, sector ETF flows.
- Charlie Bilello: historical cycle/data charts.
- Nick Timiraos: Fed/FOMC interpretation.
- ZeroHedge: contrarian/risk narrative, sentiment check.
- The Economist: global policy, elite chart view.
- IsabelNet: daily data visualization.
- FactSet: weekly higher-quality earnings/market analysis.

Reuters and Bloomberg web/login automation was blocked by bot/access restrictions. Yahoo Finance was considered a more practical news source for now.

## Dirty Files To Avoid

Do not stage or revert these unless the user explicitly asks:

- `projects/autopark/charts/*datawrapper.json`
- `projects/autopark/scripts/capture_source.mjs`
- `projects/wepoll-panic/**`
- `projects/autopark/docs/source_audits/2026-05-04-*`
- `projects/autopark/docs/source_audits/wallstengine-cdp-docker.png`
- `projects/autopark/docs/sourcebooks/2026-05-04-pipeline-sourcebook.md`

These are generated, experimental, or unrelated working artifacts from today.

## Useful Verification Commands

```powershell
python -m unittest discover -s projects/autopark/tests
python projects/autopark/scripts/build_live_notion_dashboard.py --date 2026-05-04
python projects/autopark/scripts/review_dashboard_quality.py --date 2026-05-04 --input projects/autopark/runtime/notion/2026-05-04/26.05.04.md --output-dir projects/autopark/runtime/reviews --json
docker logs --tail 80 buykings-autopark-publisher
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Suggested Starter Prompt For The Next Codex

```text
Autopark 이어서 시작.

Repo: C:\Users\User1\Documents\code\buykings
현재 기준: main, 최신 커밋 df72216f.
먼저 projects/autopark/docs/handoffs/2026-05-04-codex-handoff.md 를 읽고 현재 상태를 파악해줘.

중요:
- 1차 MVP 포맷은 고정한다.
- dirty chart JSON, Wepoll generated files, source_audits/sourcebook untracked outputs는 건드리지 않는다.
- Docker autopark publisher는 05:00 KST run / 05:20 retry / gate publish로 돌아가야 한다.
- LLM은 구조/순서/자료명/순위를 결정하지 않고 짧은 문장만 쓴다.
- OpenAI 반복 실테스트는 rate limit을 조심한다.

우선 git status, 최근 커밋, docker logs --tail 80 buykings-autopark-publisher를 확인하고 이어서 작업하자.
```
