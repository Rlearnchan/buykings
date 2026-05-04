# Autopark Source Quality Follow-up

Date: 2026-05-04  
Branch: main  
Scope: source collection quality after MVP freeze

## Summary

The first post-MVP source-quality pass is implemented and partially measured.

- Headline river works when network access is available.
- Headline river reached the configured 300-item cap.
- Balanced limiting now keeps late sources such as TradingView and Yahoo agenda expansions represented.
- Analysis river can normalize existing X posts and fetch IsabelNet/FactSet.
- X browser fallback is wired in code, but the live CDP audit timed out before collection.

## Commands

Headline river audit:

```powershell
.venv\Scripts\python.exe projects/autopark/scripts/collect_headline_river.py --date 2026-05-04 --include-support --limit-per-source 80 --overall-limit 300 --timeout 20 --output projects/autopark/docs/source_audits/2026-05-04-live-headline-river-check.json --markdown-output projects/autopark/docs/source_audits/2026-05-04-live-headline-river-check.md
```

Analysis river audit:

```powershell
.venv\Scripts\python.exe projects/autopark/scripts/collect_analysis_river.py --date 2026-05-04 --limit-per-source 20 --overall-limit 160 --timeout 20
```

X fallback audit:

```powershell
node projects/autopark/scripts/collect_x_timeline.mjs --date 2026-05-04 --run-name x-timeline-audit --source-profile market_radar --max-posts 8 --lookback-hours 72 --scrolls 2 --search-fallback --cdp-endpoint http://127.0.0.1:9222
```

## Headline River Result

Output:

- `projects/autopark/docs/source_audits/2026-05-04-live-headline-river-check.json`
- `projects/autopark/docs/source_audits/2026-05-04-live-headline-river-check.md`

Overall:

- item_count: 300
- configured source checks: 11
- agenda expansions: 5

Selected item distribution after balanced limit:

| Source | Items kept | Source status |
|---|---:|---|
| Finviz News | 47 | ok, 80 collected |
| Yahoo Finance Ticker RSS | 16 | ok, 20 collected |
| BizToc RSS | 47 | ok, 80 collected |
| BizToc Home | 46 | ok, 80 collected |
| CNBC World | 46 | ok, 80 collected |
| TradingView News | 46 | ok, 80 collected |
| Yahoo Agenda: rates/dollar | 20 | ok, 20 collected |
| Yahoo Agenda: index/breadth | 13 | ok, 20 collected |
| Yahoo Agenda: oil/risk | 13 | ok, 20 collected |
| Yahoo Agenda: AI capex | 5 | ok, 20 collected |
| Yahoo Agenda: AI earnings week | 1 | ok, 20 collected |

BizToc anomaly keywords:

- ai: 41
- hormuz: 12
- trump: 10
- rate: 7
- dow: 5
- oil: 3

Interpretation:

- Finviz is still useful as a broad baseline, but headline-only items should not dominate final selection.
- Yahoo RSS is cleaner and more structured, but ticker overlap creates dedupe pressure.
- BizToc is useful for anomaly detection. It should stay a signal source, not a high-authority evidence source.
- CNBC and TradingView are viable support pools after filtering section/navigation links.
- Balanced limiting is necessary because a simple first-300 cut starves agenda expansions.

## Analysis River Result

Output:

- `projects/autopark/docs/source_audits/2026-05-04-live-analysis-river-check.json`

Overall:

- item_count: 41
- source_count: 8

Distribution:

| Source | Items | Role | Status |
|---|---:|---|---|
| Kobeissi Letter | 11 | market_attention | ok |
| IsabelNet | 20 | chart_context | ok |
| FactSet Insight | 10 | earnings_context | ok |
| Wall St Engine | 0 | earnings_reaction | missing from local X posts |
| Bespoke | 0 | macro_chart_context | missing from local X posts |
| Charlie Bilello | 0 | macro_chart_context | missing from local X posts |
| Liz Ann Sonders | 0 | macro_chart_context | missing from local X posts |
| Kevin Gordon | 0 | macro_chart_context | missing from local X posts |

Content levels:

- headline: 20
- headline+summary: 10
- text: 1
- text+image: 10

Interpretation:

- IsabelNet and FactSet are good non-X analysis anchors.
- Current local X material is too concentrated in Kobeissi.
- The next browser collection should verify whether `--search-fallback` recovers the missing X analysis sources.

## X Fallback Check

Result:

- live CDP audit did not complete
- failure point: Playwright `connectOverCDP` timed out after websocket connection began
- this does not invalidate the code path; dry-run contract confirms `--search-fallback` is passed to the scheduled `x-timeline` command

Next check:

- restart or refresh the host browser/CDP session
- rerun the short `x-timeline-audit` command
- inspect `source_summary` for fallback collection methods and per-source item counts

## Code Adjustments Made During Audit

- Added stronger headline filters for:
  - BizToc quote links such as Yahoo Finance quote pages
  - CNBC section/category pages
  - low-signal navigation phrases
- Added balanced headline limiting so the 300-item cap does not starve late sources.
- Kept the final publish contract unchanged.

## Remaining Work

- Re-run X fallback after browser/CDP refresh.
- Tune per-source weights after one or two real 05:30 runs.
- Decide whether to split collection windows if full runtime remains too long:
  - 22:30 KST pre-open source sweep
  - 05:00 KST close-to-publish sweep
  - 05:30 KST merge, editorial, render, quality gate, Notion

