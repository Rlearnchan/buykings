# 2026-05-05 Full Rehearsal 2

## Summary

- Branch/SHA: `main` / `a2bc2e1462ab7c27e2ba90723bbecbd2bf4ac463`
- Notion title: `26.05.05 (2)`
- Run window: `2026-05-05 16:00:39-16:22:21 KST`
- Total elapsed: `21m 42s`
- Publish policy: `always`
- Notion URL: https://www.notion.so/26-05-05-2-357468fb878d81cdbd8bfef7b2192090
- Page id: `357468fb-878d-81cd-bd8b-fef7b2192090`
- Block count: `343`
- Quality gate: `pass` (`format=97`, `content=100`, `integrity=100`)

Two earlier launch attempts failed before collection because the PowerShell `--publish-title "26.05.05 (2)"` argument split at `(2)`. The successful run used `AUTOPARK_PUBLISH_TITLE='26.05.05 (2)'` inside the child PowerShell command.

## Timings

| Step | Status | Elapsed | Notes |
| --- | --- | ---: | --- |
| Preflight browser check | warn | 63.88s | Markdown/log emitted; run continued. |
| Market preflight agenda | ok | 102.53s | `gpt-5-mini`, fallback false, agenda 8. |
| News batch A | ok | 5.92s | 52 candidates, 5/5 sources ok. |
| News batch B | ok | 10.62s | 6 candidates, 7/8 sources ok. |
| X timeline | warn | 30.30s | CDP/X collection failed this run. |
| Earnings calendar X | warn | 30.31s | CDP/X collection failed this run. |
| Finviz captures | warn | 30s each | Index, S&P500 heatmap, Russell heatmap failed; publishing continued. |
| CNN/CME captures | warn | 30s each | Browser screenshot path failed; Datawrapper FedWatch succeeded. |
| Datawrapper market charts | ok | ~3-9s each | Yahoo/CoinGecko data fetched and PNGs exported. |
| Economic calendar | ok | 1.81s | 9 events; US/global Datawrapper exports succeeded. |
| Headline river | ok | 5.62s | Output generated. |
| Analysis river | ok | 1.72s | Output generated. |
| Market radar | ok | 0.38s | 329 candidates. |
| Evidence microcopy | ok | 300.30s | File generated, but both OpenAI groups timed out and fell back. |
| Market focus brief | ok | 79.81s | `gpt-5-mini`, fallback false, focuses 3, gaps 5. |
| Editorial brief | ok | 143.69s | `gpt-5-mini`, fallback false, storylines 3. |
| Media focus selection | ok | 0.31s | 30 cards selected, 15 storyline + 15 supplemental. |
| Feature stocks | warn | 60.42s / 45.28s | Yahoo trending and Finviz feature captures failed. |
| Feature stock microcopy | ok | 75.95s | Output file generated, limited by failed source collection. |
| Notion Markdown | ok | 30.52s | `runtime/notion/2026-05-05/26.05.05.md`. |
| Quality review | ok | 0.20s | Gate pass, 1 low polish finding. |
| Notion publish | ok | 72.81s | Published title `26.05.05 (2)`. |

## LLM Status

- Preflight agenda: `gpt-5-mini`, web on, 102.329s, response id `resp_0d4f26a1dab8d7a20069f995d8b8908194863c61ee273977bb`.
- Evidence microcopy: `gpt-5-mini`, 2 grouped requests of 30 items each, 150s timeout per group.
  - Group 1: `TimeoutError: The read operation timed out`, fallback 30.
  - Group 2: `TimeoutError: The read operation timed out`, fallback 30.
  - Final file includes 200 items, all fallback; unsent items marked deterministic/not sent.
- Market focus: `gpt-5-mini`, 36 candidates sent, 205,469 prompt chars, 79.296s, fallback false.
- Editorial: `gpt-5-mini`, 16 candidates sent from 329 total, 43,629 prompt chars, 143.484s, fallback false.
- Dashboard microcopy ran as part of Markdown build; rendered file passed quality gate.

## Datawrapper Timestamp Check

Market chart subtitles were unified to the run confirmation timestamp:

- `us10y`, `crude-oil-wti`, `crude-oil-brent`, `dollar-index`, `usd-krw`, `bitcoin`: `26.05.05 16:00 KST`

Exceptions kept their required suffixes:

- FedWatch short/long: `26.05.05 16:00 KST · 현재 기준금리 3.50-3.75%`
- Economic calendar US: `26.05.05 16:00 KST · 미국 2★ 이상`
- Economic calendar global: `26.05.05 16:00 KST · 미국 제외 3★`

## Media Focus

- Selection contract: `media_focus_selection_v1`
- Candidate count: `339`
- Selected cards: `30`
- Storyline bucket: `15`
- Supplemental bucket: `15`
- Selection policy confirms fixed theme terms are not used as a gate:
  - `theme_keys_usage=tag_and_diversity_only_not_gate`
  - `supplemental_terms_usage=not_used_as_gate`
- Top anomaly/keyword table was rendered under `## 2. 미디어 포커스` as `### 수집 결과`.

## Findings

- Quality gate passed but reported one low polish finding: one media-focus bullet still looked like an English source sentence (`Tariffs are high.`).
- Finviz, CNN, CME browser screenshots failed in this run. Datawrapper replacements covered FedWatch and market/economic charts, but Finviz/CNN visual capture remains unstable.
- X timeline collection failed, including earnings calendar X. This reduces the analysis-river freshness and feature stock coverage.
- Evidence microcopy remains the main LLM stability bottleneck: OpenAI likely generated server-side responses, but the client timed out reading both grouped responses.
- Yahoo trending stocks and Finviz feature stock captures failed, so `## 3. 실적/특징주` should be reviewed separately before treating the feature stock block as complete.

## Artifacts

- Main log: `projects/autopark/runtime/logs/2026-05-05/full-rehearsal-20260505-160038.log`
- Error log: `projects/autopark/runtime/logs/2026-05-05/full-rehearsal-20260505-160038.err.log`
- JSON run log: `projects/autopark/runtime/logs/2026-05-05-live-all-in-one.json`
- Markdown run log: `projects/autopark/runtime/logs/2026-05-05-live-all-in-one.md`
- Notion Markdown: `projects/autopark/runtime/notion/2026-05-05/26.05.05.md`
- Quality review: `projects/autopark/runtime/reviews/2026-05-05/dashboard-quality.json`
- State mirror: `.server-state/autopark/runs/2026-05-05`
