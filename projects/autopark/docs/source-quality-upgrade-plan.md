# Autopark Source Quality Upgrade Plan

Status: internal planning note after MVP freeze  
Date: 2026-05-04  
Scope: source collection and evidence interpretation quality, not publish-format expansion

## 1. Context

The current Autopark dashboard format is now treated as the MVP baseline:

- compact top host sheet
- fixed `## 1. 시장은 지금`
- unified `## 2. 미디어 포커스`
- separate `## 3. 실적/특징주`
- no role/id/hash exposure in publish Markdown
- depth added through host summary, storyline `왜 중요한가`, and media-focus `주요 내용`

The next phase should not make the publish page larger. The goal is to make the internal evidence warehouse better so the same compact format carries better judgement.

## 2. Core Principle

Pre-flight should not become a gate that narrows the information universe too early.

GPT can be useful for agenda discovery, but if its output directly limits later searches, it may block 박종훈 팀장의 view from entering the process. The system should therefore use GPT pre-flight as an expansion layer, not a filter.

Working rule:

- Keep a broad baseline headline river regardless of pre-flight.
- Use pre-flight only to add agenda-linked deep searches and ticker expansions.
- Let Market Radar, Market Focus, and Editorial decide after seeing the larger pool.

## 3. Proposed Source Architecture

### 3.1 News Layer

The news layer captures what the market/news flow is saying today.

#### Finviz News: baseline headline river

Role:

- Always-on headline baseline.
- Runs independently of GPT pre-flight.
- Provides a broad market headline floor.

Why:

- It prevents GPT agenda choices from shrinking the information set.
- It is market-native and good for headline-only detection.

Use:

- Store headline, link, host, source label when available.
- Treat as headline radar, not as final public evidence.
- Original article body is optional and often not needed.

#### Yahoo ticker RSS: agenda-linked deepening

Role:

- Use fixed ticker RSS plus pre-flight agenda-specific ticker expansion.
- Works best as a clean, structured feed.

Base ticker set:

- `^GSPC`, `^IXIC`, `^DJI`, `CL=F`, `^TNX`, `NVDA`, `MSFT`, `AMZN`, `GOOGL`

Agenda expansion examples:

- rates/dollar: `^TNX`, `DX-Y.NYB`, `TLT`, `IEF`, `KRE`, `XLF`
- oil/risk: `CL=F`, `BZ=F`, `XLE`, `CVX`, `XOM`, `OIH`
- AI/capex: `NVDA`, `MSFT`, `GOOGL`, `AMZN`, `META`, `AVGO`, `AMD`, `SMCI`, `VRT`, `CEG`
- Korea transmission: `EWY`, `TSM`, `ASML`, `SOXX`, `SMH`, `KRW=X`
- crypto/risk appetite: `BTC-USD`, `ETH-USD`, `COIN`, `MSTR`, `IBIT`

Use:

- Store title, URL, published time, short RSS summary, host.
- Use as fast context and candidate discovery.
- Apply original-host weighting because Yahoo RSS includes mixed external publishers.

#### BizToc Home: keyword/anomaly detector

Role:

- Detect repeated keywords, sudden names, odd themes, and cross-source anomalies.
- Do not treat every item as a strong evidence candidate.

Use:

- Extract headlines and source labels at volume.
- Count repeated entities/themes.
- Promote only when confirmed by Finviz/Yahoo/CNBC/TradingView/official data.

Good for:

- "Something is suddenly everywhere" detection.
- Early discovery of side stories.

Risk:

- Very noisy.
- Needs category, source, and keyword filters.

#### CNBC World and TradingView News: support pool

Role:

- Fill context around themes already seen in Finviz/Yahoo/BizToc.
- CNBC is broadcast-friendly.
- TradingView is ticker/sector-friendly.

Use:

- Secondary source pool.
- Good for accessible headlines and short descriptions.
- Avoid over-weighting duplicated syndicated items.

### 3.2 Analysis Layer

The analysis layer should not be mixed with fast-news sources. Each source should have a clear editorial role.

Exclude or down-rank pure news X accounts from this layer:

- Reuters X
- Bloomberg X
- WSJ X
- CNBC X

These are news distribution surfaces, not analysis sources. They may still be collected in the news layer.

Initial role map:

| Source | Layer role | Best for | Caution |
|---|---|---|---|
| Wall St Engine | earnings reaction | earnings releases, company numbers, post-earnings moves | verify numbers with company/market data |
| IsabelNet | data/chart context | valuation, positioning, sentiment, macro charts | check chart date and interpretation |
| Kobeissi Letter | market attention | what the market is loudly watching now | can be sensational; needs confirmation |
| FactSet | weekly deep analysis | earnings season, margins, EPS/revenue trend | slower cadence |
| Bespoke | breadth/statistics | breadth, seasonality, performance tables | access may vary |
| Charlie Bilello | long-run statistics | asset returns, macro comparisons, simple charts | often context rather than breaking news |
| Liz Ann Sonders | macro/market structure | economic and market charts | verify underlying source/date |
| Kevin Gordon | macro chart/context | labor, inflation, cycle details | verify source/date |
| Earnings Whispers | earnings calendar | upcoming earnings and ticker seeds | use as calendar seed, not final evidence |

## 4. Pipeline Design

### Stage A: Pre-flight Agenda

Keep:

- GPT pre-flight with web enabled.
- Output remains hypothesis-only.
- `public_safe=false`.

Change:

- Do not let pre-flight remove baseline sources.
- Add agenda-to-ticker expansion.
- Add agenda-to-query expansion only as extra collection, not replacement.

Outputs:

- `market-preflight-agenda.json`
- `headline_river_plan.json`

### Stage B: Headline River

New or refactored script:

- `collect_headline_river.py` or `collect_headline_river.mjs`

Inputs:

- fixed baseline source config
- `market-preflight-agenda.json`
- agenda ticker expansion map

Always collect:

- Finviz News headline baseline
- Yahoo base ticker RSS
- BizToc Home anomaly scan

Collect as support:

- Yahoo agenda-expanded RSS
- CNBC World
- TradingView News

Output:

`data/processed/{date}/headline-river.json`

Contract:

```json
{
  "ok": true,
  "date": "2026-05-04",
  "items": [
    {
      "item_id": "headline-...",
      "source_id": "finviz-news",
      "source_label": "Finviz News",
      "publisher": "",
      "title": "...",
      "url": "...",
      "published_at": "...",
      "snippet": "...",
      "collection_method": "html",
      "content_level": "headline",
      "agenda_links": ["agenda_oil_risk"],
      "detected_keywords": ["oil", "hormuz"],
      "source_role": "baseline_headline"
    }
  ],
  "source_stats": []
}
```

### Stage C: Analysis River

New or refactored script:

- `collect_analysis_river.py` or expand existing X/visual collection

Inputs:

- source role map
- X/browser profile collection
- RSS/HTML sources such as FactSet/IsabelNet

Output:

`data/processed/{date}/analysis-river.json`

Contract:

```json
{
  "items": [
    {
      "item_id": "analysis-...",
      "source_id": "x-kobeissiletter",
      "source_label": "Kobeissi Letter",
      "analysis_role": "market_attention",
      "title": "...",
      "summary": "...",
      "url": "...",
      "image_refs": [],
      "use_policy": "attention_signal_only"
    }
  ]
}
```

### Stage D: Evidence Microcopy

Extend current evidence microcopy to accept:

- market-radar candidates
- headline-river items
- analysis-river items

For each item, produce:

- `title`: short public label around 20 characters
- `content`: one core point in 1-3 complete sentences

Final publish still decides its own labels:

- `주요 내용` in media focus
- no internal role/id/hash exposure

### Stage E: Market Radar

Market Radar should combine:

- fixed market charts
- headline river volume
- BizToc anomaly keywords
- analysis source role
- X attention signals
- evidence microcopy summaries

Selection should not be "highest headline count wins." It should score:

- market reaction present
- multiple independent sources
- Korea-open relevance
- source authority
- PPT usefulness
- source-role fit

### Stage F: Market Focus and Editorial

Market Focus should see:

- selected radar candidates
- pre-flight agenda, marked hypothesis-only
- source roles
- evidence microcopy
- source roles and pairing rules

Editorial should decide:

- top 3 storylines
- first five minutes fit
- slide sequence

Renderer still owns:

- final structure
- order rendering
- card numbering
- public labels

## 5. Source Role Config

Add:

`projects/autopark/config/source_roles_v2.yml`

Example:

```yaml
sources:
  finviz-news:
    layer: news
    role: baseline_headline
    authority: medium
    use_policy: headline_radar
    always_collect: true

  yahoo-finance-ticker-rss:
    layer: news
    role: agenda_deepening
    authority: medium
    use_policy: fast_context
    always_collect: true

  biztoc-home:
    layer: news
    role: anomaly_detector
    authority: medium_low
    use_policy: keyword_signal

  x-kobeissiletter:
    layer: analysis
    role: market_attention
    authority: medium
    use_policy: attention_signal_only

  factset-insight:
    layer: analysis
    role: earnings_context
    authority: high
    use_policy: analysis_anchor
```

## 6. Quality Checks

Add source-layer quality checks:

- Finviz baseline missing or below minimum headline count.
- Yahoo base ticker RSS missing.
- BizToc anomaly extraction produced no keyword stats.
- Pre-flight agenda-linked Yahoo expansion failed.
- Analysis layer has no usable non-news X or research source.
- News X account mistakenly treated as analysis source.
- Source role missing for a selected media focus card.

Do not fail publish for every collection weakness. Classify:

- blocker: no baseline market/news data at all
- warning: one support source failed
- note: paywall/body access unavailable but headline exists

## 7. Implementation Order

1. Preserve MVP dashboard contract.
2. Add `source_roles_v2.yml`.
3. Build `headline_river` collector using the audit script findings.
4. Add agenda-to-ticker expansion for Yahoo RSS.
5. Add BizToc keyword/anomaly summary.
6. Split analysis sources from news sources.
7. Feed headline/analysis river into evidence microcopy.
8. Feed enriched evidence into Market Radar and Market Focus.
9. Add source-layer quality checks and sourcebook sections.

Current implementation status:

- Steps 1-5 are implemented in the headline-river/source-role layer.
- Step 6 is implemented as `collect_analysis_river.py`.
- Step 7 is wired into evidence microcopy with URL/source-title dedupe.
- Step 8 is wired into Market Radar, Market Focus, and Editorial inputs.
- Step 9 is partially implemented as warning-level quality checks and sourcebook sections.

## 8. Open Questions

- Should Yahoo News scroll be retired for now, given poor signal after filtering?
- Which Finviz News tabs should be collected daily: market, stocks, ETF, crypto?
- Should BizToc Home or BizToc RSS be the primary anomaly detector?
- Which X accounts should use profile page, and which should default to `from:handle` live search?
- Which analysis sources should default to profile page, and which should default to `from:handle` live search?

## 8.1 Future Collection Windows

If one 05:30 run becomes too slow, split collection without changing the publish contract:

- 22:30 KST: pre-open collection for news/headline river, X analysis river, and slow support sources.
- 05:00 KST: close-to-publish collection for market charts, FedWatch, calendars, fresh headlines, and late X posts.
- 05:30 KST: merge/dedupe by URL, title, source, and published time, then run Market Radar -> Evidence Microcopy -> Market Focus -> Editorial -> Renderer -> Quality Gate -> Notion.

The split should increase freshness and runtime reliability, not create two dashboards. Final sourcebook should record each collection window and which items came from it.

## 9. Current Working Judgment

Use this structure:

- Finviz News: broad baseline
- Yahoo ticker RSS: clean agenda-linked deepening
- BizToc: anomaly/keyword detection
- CNBC/TradingView: support context
- role-mapped analysis sources: editorial interpretation and PPT material

The aim is not to collect less. The aim is to collect broadly, label source purpose clearly, and let later editorial stages use the larger pool with better judgment.
