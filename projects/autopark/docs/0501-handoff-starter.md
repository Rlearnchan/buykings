# Autopark 0501 Handoff Starter

This is the single starter document for the next Codex thread. Read this first before touching code.

## Current State

Autopark has been pulled into the Windows workspace and the 2026-05-01 test run reached Notion publication.

- Project root: `projects/autopark`
- Main runner: `projects/autopark/scripts/run_live_dashboard_all_in_one.py`
- Published 0501 page: `https://app.notion.com/p/26-05-01-353468fb878d811caaf6faac86b55978`
- Local 0501 markdown: `projects/autopark/runtime/notion/2026-05-01/26.05.01.md`
- Run log: `projects/autopark/runtime/logs/2026-05-01-live-all-in-one.json`
- Post-publish review: `projects/autopark/runtime/reviews/2026-05-01/post-publish-review.json`
- Quality review: `projects/autopark/runtime/reviews/2026-05-01/dashboard-quality.json`

The latest 0501 baseline run passed the quality gate and was republished to Notion:

- `quality_gate=pass`
- `format_score=100`
- `content_score=100`
- `block_count=152`
- Earlier pages `352468fb-878d-8108-9fc2-cf57493314d2`, `353468fb-878d-81b4-93c3-c445b9dfe932`, `353468fb-878d-81d7-9968-fa70bd9dd9f5`, and `353468fb-878d-81c5-b05f-f8aa7248a2bf` were archived by `--replace-existing`.
- New page_id: `353468fb-878d-811c-aaf6-faac86b55978`
- Remaining intentional warnings: generic Polymarket skipped when no issue-specific market is configured.

## What Changed In This Thread

The main theme of the thread was moving Autopark from a Mac-ish/local prototype into a Windows workspace that can run repeatable daily test publications.

Important implemented changes:

- Added/froze the compact live dashboard format in `projects/autopark/docs/live-dashboard-format.md`.
- Removed the bulky `오늘의 핵심 키워드` block from the Notion dashboard.
- Changed market section chart headings so they show only the instrument name, not the live value.
- Changed rate deltas to basis points, for example `+4.2bp` instead of `%p`.
- Changed source/capture/publication timestamps to inline code formatting for readability in Notion.
- Changed screenshot capture labels to use actual capture times where metadata exists.
- Removed extra misc-card prompts such as `이 자료가 여는 질문` and `다음에 붙일 자료`.
- Added Korean summary behavior for image/X cards so a viewer can understand the image without reading the original post.
- Reduced Finviz feature-stock crop padding so lower ad sections are less likely to appear.
- Added one-shot Windows runner support with `ops/windows/run_autopark_once_at.ps1`.
- Added `--skip-fed-probabilities` to unblock runs when CME/FedWatch hangs.
- Moved browser-dependent collection toward one shared Autopark Chrome CDP profile:
  - `capture_source.mjs`
  - `capture_finviz_feature_stocks.mjs`
  - `run_live_dashboard_all_in_one.py`

The last browser fix was important: Earnings Whispers had still been launching a separate headed Chrome via `--profile projects/autopark/runtime/profiles/x --headed --browser-channel chrome`. It now uses the same `--cdp-endpoint` path as X timeline, Finviz, CNN, FedWatch/Polymarket, and feature-stock captures.

## Browser Rule Going Forward

Use one shared Autopark Chrome profile for all browser-dependent sites unless there is a strong reason not to.

Expected approach:

- Start Chrome through the Autopark CDP profile.
- Attach Playwright scripts with `--cdp-endpoint http://127.0.0.1:9222`.
- Do not launch separate headed Chrome windows for specific sources.
- Do not use `projects/autopark/runtime/profiles/x` as a separate login profile in the all-in-one pipeline.

Reason: the user logged into X in the visible Autopark Chrome. Separate browser profiles lose that login and make captures inconsistent.

## 0501 Run Result

The 0501 run was successful enough for a baseline:

- Notion publication worked.
- Main X timeline worked well after login: `posts=67`, `ok_sources=10/10`.
- Earnings calendar X worked: `posts=1`.
- Finviz market captures worked.
- CNN Fear & Greed capture worked.
- Datawrapper publish/export worked for:
  - US 10Y
  - WTI
  - Brent
  - DXY
  - USD/KRW
  - Bitcoin
  - US economic calendar
  - global economic calendar
- Finviz feature-stock captures worked for:
  - XLE, CVX, XOM, GOOGL, MSFT, META, AMZN, V, PI, UBER

Known warning:

- FedWatch now clicks each meeting date in the CME frame and reconstructs the `MEETING DATE x target-rate range` conditional probability matrix. The dashboard renders both a color heatmap PNG and a trimmed native Notion table, so the market-implied distribution is visible at a glance without relying on the unstable CME screenshot.
- Generic Polymarket is skipped by default unless an issue-specific market is configured.

## Main Problems Found

### 1. Browser profile fragmentation

This was the most disruptive issue.

Originally, different sources used different browser modes:

- X timeline used shared CDP Chrome.
- Finviz/CNN were moved to shared CDP Chrome.
- Earnings Whispers still launched a separate Chrome.
- Some scripts still expose `--profile`, `--headed`, and `--browser-channel` options for manual/smoke use.

Current all-in-one runner should now use shared CDP for the actual daily path. Future work should verify this by running the pipeline and checking that no extra Chrome window appears.

### 2. FedWatch capture uses table extraction, not screenshots

The user clarified that FedWatch should capture:

- The left-side `Probabilities` tab.
- The lower of the two tables in that view.

In practice, CME/FedWatch screenshots were unstable, so the pipeline now extracts the table text, reconstructs the meeting-by-rate matrix, renders a heatmap PNG, and includes a trimmed markdown table in the final dashboard. The capture remains isolated and non-blocking, but the latest 0501 baseline returned `capture cme-fedwatch: ok=True`.

### 3. Polymarket should be issue-driven, not generic

Polymarket should not always capture a generic rate market. It should be used only when a current issue has a specific market that explains the issue well.

Example rule:

- If the day is about Iran/oil, find a market that expresses that risk.
- If no useful market exists, skip Polymarket cleanly.

### 4. Reuters direct collection failed

General web news collection tried `https://www.reuters.com/` and received HTTP 401. Reuters still appeared indirectly through X and other aggregators, but direct Reuters scraping should not be treated as reliable in the current setup.

Possible next steps:

- Use Reuters X as a pointer source.
- Use BizToc/Yahoo/CNBC/TradingView for headline discovery.
- Add a dedicated search/lookup supplement when a headline needs confirmation.

### 5. English raw titles can still leak into the final page

The user strongly prefers Korean keyword-style titles.

Bad examples seen in the 0501 page:

- `Bloomberg: A draft White House AI…`
- `Tech stocks today: Tech stocks vo…`
- `$GOOGL : We are compute constrain…`

Current behavior has improved for the known 0501 leaks, but this should keep being checked on each run. Desired behavior:

- Convert raw English titles into compact Korean topic labels.
- Use the same Korean labels in the top storyline references.
- Keep source links, but do not use truncated English as the visible title.

### 6. Some source timing can be misleading

The page now formats source times as inline code, which is good. But the execution happened around `26.05.01 00:55 KST`, so some market data may be pre-close or in-progress relative to US trading.

Future work should distinguish:

- Actual capture time.
- Market data observation date.
- Whether the run is a midnight test run or morning production run.

### 7. Data volume is large but not all useful

The 0501 run collected roughly 140-160 raw/intermediate items. `market-radar` then scored and grouped 108 candidate items, but that is a derived layer, not 108 additional raw sources.

Useful:

- X market accounts for fast narrative and charts.
- Finviz/Datawrapper for market-state visuals.
- Yahoo/CNBC/BizToc for headline discovery.
- Earnings calendar plus Finviz ticker charts for feature-stock blocks.

Less useful:

- Old TradingView headlines mixed into current-day candidates.
- Isabelnet is high-quality but often background material rather than day-of news.
- Direct Reuters homepage collection currently fails.

## Source Evaluation From 0501

### X timeline

Best source group in this run. Login worked and produced 67 posts from:

- Bespoke
- Charlie Bilello
- Kobeissi Letter
- Liz Ann Sonders
- Wall St Engine
- Reuters
- Bloomberg
- CNBC
- StockMarket.News

Use for:

- Market narrative.
- Fast charts.
- Sentiment and positioning.
- News pointers.

Risk:

- Can be noisy, duplicated, exaggerated, or raw-English-heavy.
- Needs headline cleanup and sometimes confirmation.

### General web news

Batch A produced 45 candidates:

- BizToc: 8
- CNBC: 12
- Yahoo Finance: 10
- TradingView: 15
- Reuters direct: failed with 401

Use for:

- Headline sweep.
- Finding confirming articles behind X headlines.
- Filling storylines with more conventional news framing.

Risk:

- TradingView can include older headlines.
- BizToc is useful as a discovery layer, not final authority.

### Visual/background sources

Batch B produced 7 Isabelnet candidates.

Use for:

- Occasional background chart.
- Market concentration, recession probability, seasonality, valuations.

Risk:

- Too broad for the user's preferred compact format if overused.
- Better as reserve material than main page content.

### Market visuals

Finviz and Datawrapper were strong:

- Finviz index/futures and heatmaps quickly show market state.
- Datawrapper charts look consistent and suitable for Notion/PPT reuse.
- Feature-stock screenshots are useful for specific tickers.

Risk:

- Finviz ad crop needs continued visual QA.
- Datawrapper chart values are only as timely as the fetched data.

## Current Desired Format

The current compact format should be preserved unless the user says otherwise.

High-level shape:

- Page title: `yy.mm.dd`
- Compact summary.
- Recommended storylines.
- `시장은 지금`
- `오늘의 이모저모`
- `실적/특징주`

Rules:

- No `오늘의 핵심 키워드` block.
- Market subheadings show names only, not values.
- Datawrapper images may keep values inside the image.
- Source/capture/publication times should be inline code.
- Rates should show bp changes.
- Misc cards should summarize the original post/article text in Korean.
- No extra `이 자료가 여는 질문`.
- No extra `다음에 붙일 자료`.
- Korean keyword-style visible titles are preferred.

## Documents To Read Next

Read this starter first, then these only as needed:

1. `projects/autopark/docs/live-dashboard-format.md`
   - Current intended Notion format. Warning: if Korean appears mojibaked, use this starter document as the source of truth and fix that file later.

2. `projects/autopark/docs/source-intelligence-map.md`
   - Source roles and profile thinking.

3. `projects/autopark/docs/source-playbook.md`
   - How sources should be used operationally.

4. `projects/autopark/docs/autopark-operating-runbook.md`
   - General runbook for operation.

5. `projects/autopark/runtime/logs/2026-05-01-live-all-in-one.json`
   - The concrete 0501 run result and step-by-step status.

6. `projects/autopark/runtime/notion/2026-05-01/26.05.01.md`
   - The actual generated page body to inspect formatting problems.

7. `projects/autopark/data/processed/2026-05-01/market-radar.json`
   - The candidate scoring/selection layer.

8. `projects/autopark/data/processed/2026-05-01/x-timeline-posts.json`
   - The X raw collection result.

## Files Most Likely To Need Work

- `projects/autopark/scripts/run_live_dashboard_all_in_one.py`
  - Orchestration, browser routing, skip flags, publication flow.

- `projects/autopark/scripts/collect_x_timeline.mjs`
  - X account collection, CDP behavior, source profiles.

- `projects/autopark/scripts/capture_source.mjs`
  - Browser captures for Finviz, CNN, FedWatch, Polymarket.

- `projects/autopark/scripts/capture_finviz_feature_stocks.mjs`
  - Feature-stock chart capture and crop behavior.

- `projects/autopark/scripts/build_live_notion_dashboard.py`
  - Final Notion markdown format, titles, summaries, section ordering.

- `projects/autopark/scripts/build_market_radar.py`
  - Candidate scoring, grouping, source prioritization.

- `projects/autopark/scripts/fetch_market_chart_data.py`
  - Market chart values, bp formatting, observation timing.

- `ops/windows/run_autopark_daily.ps1`
  - Windows daily runner wrapper.

- `ops/windows/run_autopark_once_at.ps1`
  - One-shot scheduled test wrapper.

## Recommended Next Thread Agenda

Start with verification, then polish:

1. Run a dry run and inspect the generated command path. Confirm every browser-dependent source uses `--cdp-endpoint`.
2. Run one real test with the visible Autopark Chrome already logged into X. Confirm no extra Chrome window opens.
3. Continue issue-driven Polymarket selection work.
4. Keep tightening raw-English title leakage in `build_live_notion_dashboard.py` and/or upstream candidate normalization.
5. Keep recency filters strict so old TradingView/news items do not rank highly.
6. Re-check Finviz crop quality.
7. Compare future Notion publications against the 0501 baseline.

## Commands Used For Verification

Useful quick checks:

```powershell
.\.venv\Scripts\python.exe -m py_compile .\projects\autopark\scripts\run_live_dashboard_all_in_one.py
```

```powershell
.\.venv\Scripts\python.exe .\projects\autopark\scripts\run_live_dashboard_all_in_one.py --date 2026-05-01 --dry-run
```

```powershell
Get-Content .\projects\autopark\runtime\logs\2026-05-01-live-all-in-one.json
```

```powershell
Select-String -Path .\projects\autopark\scripts\*.py,.\projects\autopark\scripts\*.mjs -Pattern 'runtime/profiles/x|--browser-channel|--profile|--headed|cdp-endpoint'
```

## Final Working Assumption

Autopark is successfully imported and basically working on Windows. The next phase should not be about rebuilding it. It should be about tightening reliability, browser-profile consistency, source filtering, visual QA, and final-page editorial quality.
