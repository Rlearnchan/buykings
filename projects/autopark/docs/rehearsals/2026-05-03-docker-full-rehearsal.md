# 2026-05-03 Docker Full Rehearsal

- Run title: `(리허설) 26.05.03`
- Branch: `codex/autopark-compact-publish-dashboard`
- Head before rehearsal patches: `136b64c2f085e171bb48c3da37e84d167d83899c`
- Docker image: `buykings-autopark:local`
- Image id: `sha256:8b3a672c3e8d3ac29f153a73143a2c208e8b87e621f2b0e0fee5fe72cfd3d479`
- Rehearsal state: `.server-state/autopark-rehearsal-20260503-203734/`
- Artifact mirror: `.server-state/autopark-rehearsal-20260503-203734/state/runs/2026-05-03/`

## Summary

The Docker rehearsal ran from fresh isolated volumes and exited `0`, but it did not publish to Notion. The quality gate returned `needs_revision` because Finviz index futures and CME FedWatch did not produce required market cards. With `AUTOPARK_PUBLISH_POLICY=gate`, the all-in-one runner correctly skipped Notion publish.

Outer stopwatch: `00:16:27.21` / `987.21s`

Internal run window: `2026-05-03T20:40:04+09:00` to `2026-05-03T20:56:30+09:00`

## Environment

- `AUTOPARK_DATE=2026-05-03`
- `AUTOPARK_SKIP_PUBLISH=0`
- `AUTOPARK_PUBLISH_POLICY=gate`
- `AUTOPARK_PUBLISH_TITLE=(리허설) 26.05.03`
- `AUTOPARK_SKIP_DATAWRAPPER_EXPORT=0`
- `AUTOPARK_EVIDENCE_MICROCOPY_ENABLED=1`
- `AUTOPARK_EVIDENCE_MICROCOPY_MODEL=gpt-5-mini`
- `AUTOPARK_MICROCOPY_ENABLED=1`
- `AUTOPARK_MICROCOPY_MODEL=gpt-5-mini`
- `AUTOPARK_STEP_TIMEOUT=240`

Only browser auth/session state was reused through `autopark-browser`. The generated `data`, `runtime`, `prepared`, and `exports` paths used fresh named Docker volumes.

## Build And Harness

- Initial Docker build failed because `.codex-worktrees/` was included in the build context and contained an unreadable temp path.
- Added `.codex-worktrees/` to `.dockerignore`; rebuild succeeded.
- `autopark-browser` initially restarted because Docker shell scripts had CRLF line endings. Normalized `ops/docker/*.sh` to LF and added `.gitattributes` to keep them LF.
- `autopark-browser` then reached `healthy`.
- The one-off run used `docker compose run --rm autopark-publisher bash ops/docker/autopark_run.sh`, not the scheduler loop.

## Step Timing

| Step | Status | Seconds | Summary |
|---|---:|---:|---|
| resolve broadcast calendar | ok | 0.00 | mode=no_broadcast; publish_policy=gate |
| preflight | ok | 48.25 | preflight log generated |
| build market preflight agenda | ok | 78.47 | fallback=False; agenda=8 |
| collect news batch a | ok | 4.31 | candidates=48; ok_sources=4/5 |
| collect news batch b | ok | 10.33 | candidates=8; ok_sources=7/8 |
| collect x timeline | ok | 105.91 | posts=35; ok_sources=10/10 |
| collect earnings calendar x | ok | 9.08 | posts=1; ok_sources=1/1 |
| build visual cards | ok | 0.04 | cards=6 |
| capture finviz-index-futures | warn | 18.07 | ok=False |
| capture finviz-sp500-heatmap | warn | 18.06 | ok=False |
| capture finviz-russell-heatmap | warn | 18.14 | ok=False |
| capture cnn-fear-greed | ok | 3.37 | ok=True |
| capture cme-fedwatch | warn | 0.38 | ok=False |
| prepare fedwatch datawrapper splits | warn | 0.04 | raw table header not found |
| market chart fetch/publish/export | ok | 73.34 | 6 market charts exported |
| economic calendar fetch/publish/export | ok | 12.26 | 2 calendar images exported |
| build market radar | ok | 0.08 | candidates=76 |
| build evidence microcopy | ok | 225.43 | output generated |
| build market focus brief | ok | 90.98 | fallback=False; focuses=4; gaps=5 |
| build editorial brief | ok | 121.42 | fallback=True; OpenAI 429 |
| capture finviz feature stocks | warn | 142.23 | all tickers blocked by Finviz challenge |
| build notion markdown | ok | 1.29 | markdown generated |
| review dashboard quality | warn | 0.06 | gate=needs_revision; format=36; content=100 |
| publish notion | warn | 0.00 | skipped: quality gate is needs_revision |
| state mirror | ok | 0.00 | 36 files copied to `/state/runs/2026-05-03` |

## Data Flow Inventory

- Raw files in isolated Docker volume: `34`
- Processed files mirrored: `16`
- Prepared CSVs mirrored: `9`
- Exported PNGs mirrored: `8`
- Market radar candidates: `76`
- Evidence microcopy:
  - source: `openai_responses_api`
  - model: `gpt-5-mini`
  - request_count: `3`
  - item_count: `76`
  - fallback_count: `30`
  - invalid_output_count: `0`
- Market Focus:
  - model: `gpt-5.5`
  - fallback: `False`
  - focuses: `4`
  - source gaps: `5`
- Editorial:
  - fallback: `True`
  - reason: `HTTPError: HTTP Error 429: Too Many Requests`
  - final storyline count in step summary: `3`

Raw collection included news batches, X timeline, earnings calendar X, Finviz captures, CME FedWatch, CNN Fear & Greed, Yahoo market data, and TradingEconomics calendar HTML.

## Quality Gate

Result: `needs_revision`

- format_score: `36`
- content_score: `100`
- finding_count: `4`

Findings:

- `COMPACT-044`: required market cards missing: main index flow, FedWatch short-term probability, FedWatch long-term probability.
- `COMPACT-030`: main index flow 2 images missing.
- `COMPACT-031`: FedWatch short/long cards missing. The finding appeared twice.

Root blockers:

- Finviz rendered `Just a moment...` / blocked pages for feature stock capture and returned `ok=False` for the three fixed Finviz market captures.
- CME FedWatch raw capture existed but did not contain the expected table header, so short/long split generation was skipped.
- Editorial fell back after OpenAI 429, but this did not block the gate.

Additional observation:

- The Docker-generated Markdown/review text showed mojibake in Korean labels in the mirrored artifacts. This should be treated as a publish blocker until the Docker text encoding path is checked, even if the missing chart cards are fixed.

## Notion Publish

No Notion page was created.

- Expected title if gate passed: `(리허설) 26.05.03`
- `notion_url`: `null`
- publish payload: `{}`
- Original `26.05.03` page was not archived or replaced because publish was skipped before calling the Notion API.
- Local publisher dry-run with `--title "(리허설) 26.05.03"` returned title `(리허설) 26.05.03`, `block_count=143`, `chunk_count=2`.

## Freshness Proof

- The run created fresh Docker named volumes:
  - `buykings_autopark_rehearsal_20260503_203734_data`
  - `buykings_autopark_rehearsal_20260503_203734_runtime`
  - `buykings_autopark_rehearsal_20260503_203734_prepared`
  - `buykings_autopark_rehearsal_20260503_203734_exports`
- Host `projects/autopark/data`, `runtime`, `prepared`, `exports/current`, and chart JSON dirty files were not mounted into the runner/publisher.
- Only `.server-state/autopark-browser` was reused for browser auth/session state.
- The rehearsal mirror is under `.server-state/autopark-rehearsal-20260503-203734/state/runs/2026-05-03/`.

## Next Fixes

1. Fix Docker Korean text encoding before any Docker publish attempt.
2. Improve Finviz challenge handling for the shared CDP browser profile, or add a clear operator intervention path when Finviz returns `Just a moment...`.
3. Harden CME FedWatch capture/parsing so a bad raw table produces a useful diagnostic and does not silently remove both required cards.
4. Consider lowering editorial retry pressure after evidence microcopy, because this run hit OpenAI 429 after a large first prompt.
