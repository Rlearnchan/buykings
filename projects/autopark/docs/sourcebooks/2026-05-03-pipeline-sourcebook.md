# 26.05.03 Autopark Pipeline Sourcebook

- Generated at: `26.05.03 19:20`
- Scope: end-to-end sourcebook for the compact dashboard pipeline: collection, API reasoning, filtering, renderer decisions, and quality gate.
- Hygiene: credentials, browser/session data, signed URLs, raw HTML, full article bodies, and full X text are not included.
- Long source material is represented as title/source/role/URL/summary only.

## 0. Artifact Inventory
- `projects\autopark\data\processed\2026-05-03\dashboard-microcopy-context.json` (12,391 bytes)
- `projects\autopark\data\processed\2026-05-03\dashboard-microcopy.json` (7,640 bytes)
- `projects\autopark\data\processed\2026-05-03\earnings-calendar-tickers.json` (29,821 bytes)
- `projects\autopark\data\processed\2026-05-03\earnings-calendar-x-posts.json` (9,581 bytes)
- `projects\autopark\data\processed\2026-05-03\earnings-ticker-drilldown.json` (76,030 bytes)
- `projects\autopark\data\processed\2026-05-03\economic-calendar.json` (300 bytes)
- `projects\autopark\data\processed\2026-05-03\editorial-brief.json` (33,041 bytes)
- `projects\autopark\data\processed\2026-05-03\finviz-feature-stocks.json` (28,258 bytes)
- `projects\autopark\data\processed\2026-05-03\market-focus-brief.json` (4,832 bytes)
- `projects\autopark\data\processed\2026-05-03\market-preflight-agenda.json` (30,343 bytes)
- `projects\autopark\data\processed\2026-05-03\market-radar.json` (295,780 bytes)
- `projects\autopark\data\processed\2026-05-03\today-misc-batch-a-candidates.json` (69,843 bytes)
- `projects\autopark\data\processed\2026-05-03\today-misc-batch-b-candidates.json` (16,073 bytes)
- `projects\autopark\data\processed\2026-05-03\visual-cards.json` (9,035 bytes)
- `projects\autopark\data\processed\2026-05-03\x-timeline-posts.json` (134,101 bytes)
- `projects\autopark\runtime\notion\2026-05-03\26.05.03.md` (12,997 bytes)

## 1. Pipeline Order
- Pre-flight Market Agenda: web-enabled discovery agenda and collection targets
- News batch A/B: collect candidate news and record source failures
- X/earnings timeline: collect X timeline posts and earnings calendar context
- Visual cards and captures: collect Finviz, market charts, FedWatch, Fear & Greed, and chart exports
- Market Radar: merge local candidates into a candidate DB with internal source/evidence roles
- Market Focus Brief: call OpenAI with sanitized local packet; no web_search; promote only local-evidence-backed focus items
- Editorial Brief: turn focus/radar into broadcast storylines and material queue
- Fixed compact renderer: LLM supplies values; renderer owns section structure/order/exposed fields
- Quality gate: validate compact host area, collection structure, forbidden tokens, and media label matching

## 2. Pre-flight Market Agenda
- Input: `target_date=2026-05-03`, `with_web=True`
- Model: `gpt-5.5`, fallback: `False`
- Public-use guard: `[{'reason': '프리플라이트는 로컬 evidence_id가 없고 웹 발견 힌트만 포함함.', 'rule': 'No agenda item is public-safe; final dashboard must cite later Market Focus Brief/local packet only.'}, {'reason': '웹 검색 결과의 수치·헤드라인은 검증 전 오염 가능성이 있음.', 'rule': 'Do not quote discovered numbers or causal claims publicly until captured in local evidence.'}, {'reason': 'X/social은 포지셔닝과 관심도 확인용이며 사실 검증 자료가 아님.', 'rule': 'Never use X posts as factual evidence; use only as sentiment check.'}, {'reason': '차트는 반응 확인용이며 원인 증명 자료가 아님.', 'r…`
- agenda_items: `8`
- collection_priorities: `4`
- raw response path: `projects\autopark\runtime\openai-responses\2026-05-03-market-preflight-raw.json`
- raw response size: `31,253` bytes
- raw_response_id: `resp_063c14e210d6404b0069f6cc4d9590819688e6843bf92c3a39`
- model: `gpt-5.5`
- top keys: `agenda, model, raw_response_id, source, web_sources`
- `agenda` keys: `agenda_items, collection_priorities, date, do_not_use_publicly, preflight_summary, source_gaps_to_watch`

| rank | agenda_id | market_question | collection_targets | why_to_check |
| --- | --- | --- | --- | --- |
| 1 | agenda_rates_dollar | 미 10년물·DXY·USD/KRW가 주식 사상권 랠리를 제약하는가, 아니면 위험선호를 확인하는가? | chart:US10Y yield 5D/1M, DXY 5D/1M, USDKRW 5D/1M overlay; market_reaction:S&P500 vs Nasdaq100 vs US10Y intraday reaction ar…; official_source:Federal Reserve latest FOMC statement… | 발견 힌트상 주식은 강하지만 채권시장은 인플레·유가·Fed 경로를 더 경계할 수 있음. 한국 개인투자자에게 환율과 성장주 할인율이 1차 체크포인트. |
| 2 | agenda_oil_risk | WTI·Brent 급등/되돌림이 인플레 기대와 섹터 로테이션을 다시 흔드는가? | chart:WTI front month, Brent front month, RBOB gasoline…; market_reaction:XLE, XOP, OIH, JETS, Dow Transports 5D relative p…; chart:US 5Y breakeven, 10Y breakeven, US10Y real yiel… | 발견 힌트상 중동·Hormuz 관련 유가 변동성이 큰 상태. 한국 시청자에게 항공·해운·정유·화학·인플레 재점화 리스크가 직접 연결됨. |
| 3 | agenda_equity_breadth | S&P500·Nasdaq 신고가성 흐름이 대형 기술주 집중 랠리인가, Russell2000·동일가중까지 확산된 랠리인가? | chart:S&P500, Nasdaq Composite, Dow, Russell2000 1D/5D/…; chart:RSP/SPY ratio, QQQ equal weight vs QQQ, IWM/SPY r…; market_reaction:S&P500 sector performance 2026-05-01 and weekly… | 지수 레벨만으로는 방송 리드가 약함. 폭과 참여율을 봐야 ‘건강한 상승’인지 ‘빅테크 의존’인지 구분 가능. |
| 4 | agenda_ai_capex | 빅테크 AI capex 증액은 반도체·전력·데이터센터 수혜로 해석되는가, FCF 압박으로 해석되는가? | chart:GOOGL MSFT AMZN META AAPL NVDA AVGO AMD SMCI VRT…; market_reaction:SOX index vs Nasdaq100 vs Cloud ETF vs Data cente…; official_source:Alphabet Microsoft Amazon Meta Q1 2026… | 발견 힌트상 Alphabet·Microsoft·Amazon·Meta 실적 이후 시장은 AI 매출 증거와 capex 부담을 차별 평가 중. 한국 반도체 투자자에게 핵심 소재. |
| 5 | agenda_semis_earnings | 이번 주 AMD·AI 인프라 실적이 ‘AI 수요 지속’ 확인인지, 높아진 기대치 부담인지? | official_source:AMD Q1 2026 earnings date, webcast, investor rela…; news_search:May 2026 AMD earnings preview AI GPU data center…; chart:AMD vs NVDA vs SOXX vs SMH 1M and YTD; mar… | 빅테크 capex 이후 다음 검증은 GPU·서버·전력·네트워킹 공급망. 한국 반도체주 오프닝에 연결될 가능성 큼. |
| 6 | agenda_apple_supply_chain | Apple 실적 반응은 소비 하드웨어 회복인가, 메모리·부품 제약 신호인가? | official_source:Apple Q1/FY2026 latest earnings release transcrip…; chart:AAPL 1D/5D, Apple suppliers basket: QCOM AVGO SWK…; news_search:Apple earnings May 2026 memory constraint… | 발견 힌트상 Apple 관련 이익 서프라이즈와 공급 제약 언급 가능성이 있음. 한국 IT 부품·메모리 투자자에게 단기 재료가 될 수 있음. |
| 7 | agenda_us_data_week | 이번 주 ISM 서비스·JOLTS·고용 관련 지표가 Fed 인하 기대를 밀어내는가, 경기둔화 우려를 키우는가? | official_source:BLS Employment Situation April 2026 release sched…; official_source:ISM Services PMI April 2026 release schedule; official_source:BLS JOLTS March 2026 release sche… | 방송일 이후 발표될 지표가 금리·달러·성장주 리스크의 다음 촉매. 일정형 아젠다로 짧게 배치 가능. |
| 8 | agenda_korea_cross_market | 미국 마감 후 한국 개장에 가장 직접 전이될 변수는 환율, 반도체, 유가 중 무엇인가? | chart:EWY, MSCI Korea ETF, USDKRW, KOSPI200 futures, Ph…; market_reaction:Samsung Electronics, SK Hynix, Hyundai Motor, Kor…; capture:PPT heatmap: Korea-linked US overnight proxie… | 한국 개인투자자 방송은 미국 뉴스보다 국내 개장 전이 더 중요. USD/KRW·EWY·반도체 ADR·유가 민감 업종을 연결해야 함. |

### preflight_downgrade_trace
- Internal trace only; not rendered in publish Markdown.
| rank | agenda_id | status | trace_destination | market_question |
| --- | --- | --- | --- | --- |
| 1 | agenda_rates_dollar | public_focus | Market Focus public item | 미 10년물·DXY·USD/KRW가 주식 사상권 랠리를 제약하는가, 아니면 위험선호를 확인하는가? |
| 2 | agenda_oil_risk | public_focus | Market Focus public item | WTI·Brent 급등/되돌림이 인플레 기대와 섹터 로테이션을 다시 흔드는가? |
| 3 | agenda_equity_breadth | downgraded | source_gap | S&P500·Nasdaq 신고가성 흐름이 대형 기술주 집중 랠리인가, Russell2000·동일가중까지 확산된 랠리인가? |
| 4 | agenda_ai_capex | source_gap | source_gap (not confirmed by local evidence) | 빅테크 AI capex 증액은 반도체·전력·데이터센터 수혜로 해석되는가, FCF 압박으로 해석되는가? |
| 5 | agenda_semis_earnings | source_gap | source_gap (not confirmed by local evidence) | 이번 주 AMD·AI 인프라 실적이 ‘AI 수요 지속’ 확인인지, 높아진 기대치 부담인지? |
| 6 | agenda_apple_supply_chain | local_evidence_only | collected locally but not promoted | Apple 실적 반응은 소비 하드웨어 회복인가, 메모리·부품 제약 신호인가? |
| 7 | agenda_us_data_week | source_gap | source_gap (not confirmed by local evidence) | 이번 주 ISM 서비스·JOLTS·고용 관련 지표가 Fed 인하 기대를 밀어내는가, 경기둔화 우려를 키우는가? |
| 8 | agenda_korea_cross_market | public_focus | Market Focus public item | 미국 마감 후 한국 개장에 가장 직접 전이될 변수는 환율, 반도체, 유가 중 무엇인가? |

## 3. News / X / Earnings Collection
### News batch A
- captured_at: `2026-05-03T13:18:44+09:00`
- lookback_hours: `48`
- require_recent_signal: `False`
- collected_count: `47`

| source | status | count | error/fallback |
| --- | --- | --- | --- |
| BizToc | ok |  |  |
| International Business, World News & Global Stock Market Analysis | ok |  |  |
| Yahoo Finance - Stock Market Live, Quotes, Business & Finance News | ok |  |  |
| Reuters / Breaking International News & Views | error |  | curl: (22) The requested URL returned error: 401 |
| Financial News & Top Stories — Market Analysis — TradingView | ok |  |  |

Representative candidates
| # | title/headline | source | role | url |
| --- | --- | --- | --- | --- |
| 1 | Apple's stock gains as company execs cite iPhone, Mac demand in boosting guidance | International Business, World News & Global Stock Market Analysis |  | https://www.cnbc.com/2026/05/01/apple-stock-rallies-on-q2-earnings-and-q3-guidance.html |
| 2 | Cramer: The market powered through a tough earnings week, we're not 'out of the woods yet' | International Business, World News & Global Stock Market Analysis |  | https://www.cnbc.com/2026/05/01/cramer-look-ahead-earnings.html |
| 3 | Exxon Mobil CEO expects higher oil prices due to Iran war: ‘The market hasn’t seen the full impact’ | International Business, World News & Global Stock Market Analysis |  | https://www.cnbc.com/2026/05/01/exxon-ceo-iran-war-oil-strait-hormuz.html |
| 4 | Jobs and earnings will dominate the first full week of May. Here's what's ahead | International Business, World News & Global Stock Market Analysis |  | https://www.cnbc.com/2026/05/01/stock-market-next-week-outlook-for-may-4-8-2026.html |
| 5 | The market isn't grading all Big Tech earnings the same — here's why | International Business, World News & Global Stock Market Analysis |  | https://www.cnbc.com/2026/05/01/the-market-isnt-grading-all-big-tech-earnings-the-same-heres-why.html |
| 6 | 1 hour ago Stock Story Ameresco (AMRC) Q1 Earnings: What To Expect | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/stockstory:d70fdfbc5094b:0-ameresco-amrc-q1-earnings-what-to-expect |
| 7 | 1 hour ago Stock Story BWX (BWXT) To Report Earnings Tomorrow: Here Is What To Expect | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/stockstory:5234a581d094b:0-bwx-bwxt-to-report-earnings-tomorrow-here-is-what-to-expect |
| 8 | 1 hour ago Stock Story BioMarin Pharmaceutical (BMRN) Reports Earnings Tomorrow: What To Expect | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/stockstory:5f5ad2361094b:0-biomarin-pharmaceutical-bmrn-reports-earnings-tomorrow-what-to-expect |
| 9 | 1 hour ago Stock Story Black Stone Minerals (BSM) To Report Earnings Tomorrow: Here Is What To Expect | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/stockstory:1d809c6d7094b:0-black-stone-minerals-bsm-to-report-earnings-tomorrow-here-is-what-to-expect |
| 10 | 1 hour ago Stock Story Boise Cascade (BCC) Reports Q1: Everything You Need To Know Ahead Of Earnings | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/stockstory:32d54528b094b:0-boise-cascade-bcc-reports-q1-everything-you-need-to-know-ahead-of-earnings |

### News batch B
- captured_at: `2026-05-03T13:18:50+09:00`
- lookback_hours: `72`
- require_recent_signal: `False`
- collected_count: `8`

| source | status | count | error/fallback |
| --- | --- | --- | --- |
| The Global Markets Channel - Advisor Perspectives | error |  | curl: (22) The requested URL returned error: 403 |
| FactSet Insight - Commentary and research from our desk to yours | ok |  |  |
| Blog – ISABELNET | ok |  |  |
| (16) Bespoke (@bespokeinvest) / X | ok |  |  |
| (16) StockMarket.News (@_Investinq) / X | ok |  |  |
| (13) The Kobeissi Letter (@KobeissiLetter) / X | ok |  |  |
| (16) Liz Ann Sonders (@LizAnnSonders) / X | ok |  |  |
| (16) Nick Timiraos (@NickTimiraos) / X | ok |  |  |

Representative candidates
| # | title/headline | source | role | url |
| --- | --- | --- | --- | --- |
| 1 | U.S. Stock Market Bull and Bear Indicator – S&P 500 | Blog – ISABELNET |  | https://www.isabelnet.com/u-s-stock-market-bull-and-bear-indicator |
| 2 | S&P 500 Earnings Season Update: May 1, 2026 | FactSet Insight - Commentary and research from our desk to yours |  | https://insight.factset.com/sp-500-earnings-season-update-may-1-2026 |
| 3 | Auto Insurers’ Profits Could Increase Given Persistently High Gas Prices | FactSet Insight - Commentary and research from our desk to yours |  | https://insight.factset.com/auto-insurers-profits-could-increase-given-persistently-high-gas-prices |
| 4 | % of Companies with Revenue Exposure to Just One Sector (TOPIX 500, MXAPJ, STOXX 600, S&P 500) | Blog – ISABELNET |  | https://www.isabelnet.com/of-sp-500-companies-guiding-next-quarter-eps-above-consensus |
| 5 | S&P 500 Performance After April >5% | Blog – ISABELNET |  | https://www.isabelnet.com/sp-500-performance-after-april-5 |
| 6 | S&P 500 Returns in April | Blog – ISABELNET |  | https://www.isabelnet.com/sp-500-returns-in-april |
| 7 | Smoothed U.S. Recession Probabilities | Blog – ISABELNET |  | https://www.isabelnet.com/smoothed-u-s-recession-probabilities |
| 8 | WTI Oil Prices in Real Terms | Blog – ISABELNET |  | https://www.isabelnet.com/the-cost-of-a-barrel-of-oil-in-real-u-s-dollar-terms |

### X timeline
- captured_at: `2026-05-03T04:19:03.102Z`
- lookback_hours: `48`
- require_recent_signal: `None`
- collected_count: `86`

| source | status | count | error/fallback |
| --- | --- | --- | --- |
| (16) Bespoke (@bespokeinvest) / X | ok |  |  |
| (2) Charlie Bilello (@charliebilello) / Twitter | ok |  |  |
| (16) StockMarket.News (@_Investinq) / X | ok |  |  |
| (21) Kevin Gordon (@KevRGordon) / X | ok |  |  |
| (13) The Kobeissi Letter (@KobeissiLetter) / X | ok |  |  |
| (16) Liz Ann Sonders (@LizAnnSonders) / X | ok |  |  |
| (16) Wall St Engine (@wallstengine) / X | ok |  |  |
| Reuters (@Reuters) / X | ok |  |  |
| Bloomberg (@business) / X | ok |  |  |
| CNBC (@CNBC) / X | ok |  |  |

Representative candidates
| # | title/headline | source | role | url |
| --- | --- | --- | --- | --- |
| 1 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050660296553840716 |
| 2 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050286082734932276 |
| 3 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050286289291714824 |
| 4 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050283700940611807 |
| 5 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050262824576786594 |
| 6 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050233055902609731 |
| 7 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050220859948741074 |
| 8 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050220254849122666 |
| 9 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050220264810578231 |
| 10 |  | (16) Bespoke (@bespokeinvest) / X |  | https://x.com/bespokeinvest/status/2050220266500849824 |

### Economic / earnings / feature-stock support
- economic-calendar events: `0`, countries: `CA, CN, DE, ES, EU, FR, GB, JP, KR, US`
- earnings ticker drilldown tickers: `68`
- finviz feature stocks: `10`
| # | title/headline | source | role | url |
| --- | --- | --- | --- | --- |
| 1 | XLE - State Street Energy Select Sector SPDR ETF Stock Price and Quote | XLE |  | https://finviz.com/quote.ashx?t=XLE&p=d |
| 2 | CVX - Chevron Corp Stock Price and Quote | CVX |  | https://finviz.com/quote.ashx?t=CVX&p=d |
| 3 | XOM - Exxon Mobil Corp Stock Price and Quote | XOM |  | https://finviz.com/quote.ashx?t=XOM&p=d |
| 4 | GOOGL - Alphabet Inc Stock Price and Quote | GOOGL |  | https://finviz.com/quote.ashx?t=GOOGL&p=d |
| 5 | MSFT - Microsoft Corp Stock Price and Quote | MSFT |  | https://finviz.com/quote.ashx?t=MSFT&p=d |
| 6 | META - Meta Platforms Inc Stock Price and Quote | META |  | https://finviz.com/quote.ashx?t=META&p=d |
| 7 | AMZN - Amazon.com Inc Stock Price and Quote | AMZN |  | https://finviz.com/quote.ashx?t=AMZN&p=d |
| 8 | V - Visa Inc Stock Price and Quote | V |  | https://finviz.com/quote.ashx?t=V&p=d |

## 4. Visual Cards / Captures / Charts
- visual cards: `6`
- visual stats: `{"candidate_count": 6, "image_count": 6, "fetched_pages": 0, "fetch_errors": 0}`
- screenshots: `11` under `projects\autopark\runtime\screenshots\2026-05-03`
- chart exports: `11` under `projects\autopark\exports\current`
| kind | file |
| --- | --- |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\cnn-fear-greed-gauge.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\cnn-fear-greed.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-index-futures-1.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-index-futures-2.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-index-futures.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-russell-heatmap-map-fallback.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-russell-heatmap-map.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-russell-heatmap.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-sp500-heatmap-map-fallback.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-sp500-heatmap-map.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-sp500-heatmap.png |
| chart | projects\autopark\exports\current\bitcoin.png |
| chart | projects\autopark\exports\current\crude-oil-brent.png |
| chart | projects\autopark\exports\current\crude-oil-wti.png |
| chart | projects\autopark\exports\current\dollar-index.png |
| chart | projects\autopark\exports\current\economic-calendar-global.png |
| chart | projects\autopark\exports\current\economic-calendar-us.png |
| chart | projects\autopark\exports\current\fedwatch-conditional-probabilities-long-term.png |
| chart | projects\autopark\exports\current\fedwatch-conditional-probabilities-short-term.png |
| chart | projects\autopark\exports\current\fedwatch-conditional-probabilities.png |
| chart | projects\autopark\exports\current\us10y.png |
| chart | projects\autopark\exports\current\usd-krw.png |

## 5. Market Radar Merge / Selection
- generated_at: `2026-05-03T13:24:00`
- candidate_count: `136`
- storylines in radar: `5`
- Internal role/id fields remain available for audit, but are not rendered in publish Markdown.
| id | title | source | source_role | evidence_role |
| --- | --- | --- | --- | --- |
| https://x.com/KobeissiLetter/status/2050710022938558611 | BREAKING: President Trump says he will be reviewing the plan that Iran has sent to the US but “can’t imagine that it wou | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050376010269634723 | Apple raised the Mac mini’s starting price to $799 from $599 after AI demand and chip supply constraints drained invento | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/_Investinq/status/2050070498306904444 | Mark Cuban's raising a question that a lot of people are asking about the biggest infrastructure build in human history. | (16) StockMarket.News (@_Investinq) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050372648077865429 | TRUMP ON IRAN: MAYBE BETTER OFF NOT MAKING A DEAL | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050722187884089775 | The US government's cash balance is rising: The Treasury General Account (TGA) is up to ~$1 trillion, the highest since | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050551657206034656 | BERKSHIRE CASH HITS RECORD $397B Berkshire Hathaway’s cash pile rose to a record $397B in Greg Abel’s first quarter as C | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050669462924247072 | BREAKING: The average price of a gallon of gas in the US surges to $4.43/gallon, now up +61% since December. Americans w | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050381071158747512 | CLAUDE CAN NOW WATCH THE MARKETS 24/7 I tested it with an AI Scoreboard brief. Every weekday at 8:30 a.m. ET, it emails: | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050552345931755921 | OPENAI CFO SARAH FRIAR WEIGHS 2027 IPO TIMING WSJ reports Friar helped keep OpenAI’s Microsoft deal on track and has pri | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/Reuters/status/2050774856640127425 | Trump says there is possibility US could restart strikes on Iran http:// reut.rs/48BvjKG | Reuters (@Reuters) / X | sentiment_probe | sentiment |
| https://x.com/business/status/2050770083039883365 | Vietnam’s inflation picked up more than expected in April, as a surge in global energy prices driven by the Iran war beg | Bloomberg (@business) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050656606791291230 | BREAKING: Tether purchased +6 tonnes of gold in Q1 2026, bringing total holdings to a record 132 tonnes, now worth ~$19. | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050740932224692732 | Biopharma M&A reached $84B in Q1, nearly double $44.4B a year ago, putting 2026 on pace for its strongest dealmaking yea | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/TKL_Adam/status/2050607483803013594 | Efficient, free markets had a solution to avoid the Spirit Airlines implosion. Instead, the worst possible outcome was c | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050696828434202649 | Investors are flooding into US Industrial and Infrastructure ETFs at a historic pace: Industrials sector ETFs have attra | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050630474129719568 | Tech layoffs are skyrocketing: Tech companies announced 81,747 layoffs in Q1 2026, the highest quarterly total since at | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/KobeissiLetter/status/2050603984939889068 | This is truly unfortunate: In 2022, JetBlue had agreed to merge with Spirit Airlines in a $3.8 billion transaction. This | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| isabelnet-com-blog-013 | WTI Oil Prices in Real Terms | Blog – ISABELNET | data_anchor | data |
| https://x.com/bespokeinvest/status/2050220254849122666 | Apple $AAPL reported its second triple play in three quarters, the first two for the company since the onset of the pand | (16) Bespoke (@bespokeinvest) / X | sentiment_probe | sentiment |
| https://x.com/charliebilello/status/2050598689849143303 | Average 30-Year Mortgage Rate in the US… 1970s: 8.9% 1980s: 12.7% 1990s: 8.1% 2000s: 6.3% 2010s: 4.1% 2020s: 5.3% --- Al | (2) Charlie Bilello (@charliebilello) / Twitter | sentiment_probe | sentiment |
| https://x.com/Reuters/status/2050777376536101213 | Recent inflation data was 'bad news,' Fed's Goolsbee says http:// reut.rs/4w0TRXv | Reuters (@Reuters) / X | sentiment_probe | sentiment |
| https://x.com/business/status/2050740299614335408 | The list of Asian stocks that benefit from business partnership with Nvidia is getting longer, as the region further int | Bloomberg (@business) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050349249188278280 | WSJ: GameStop is preparing an offer for eBay, with Ryan Cohen reportedly building a stake ahead of a potential bid. The | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
| https://x.com/CNBC/status/2050587179680665948 | Airfare amid Iran war: Buy now or wait out the conflict? Experts weigh the risks | CNBC (@CNBC) / X | sentiment_probe | sentiment |
| https://x.com/charliebilello/status/2050587363731272009 | Apple has bought back $732 billion in stock over the past 10 years, which is greater than the market cap of 488 companie | (2) Charlie Bilello (@charliebilello) / Twitter | sentiment_probe | sentiment |

## 6. Market Focus Brief API
- Input: market-radar/local candidates + preflight agenda + sanitized local packet
- Model: `fixture`, fallback: `False`, with_web: `False`
- focus_count: `2`
- source_gap_count: `1`
- raw_response_id: ``
### Sanitized prompt check
- model: `gpt-5.5`
- with_web: `False`
- prompt_chars: `78265`
- http_url_count: `0`
- signed_url_hits: `0`
- local_path_hits: `6`
- body_like_key_hits: `0`
- ev_alias_count: `316`
- input_payload_keys: `available_assets, charts, date, input_limits, market_preflight_agenda, market_radar, packet_mode, policy, raw_sources, visual_cards`
- raw response path: `projects\autopark\runtime\openai-responses\2026-05-03-market-focus-raw.json`
- raw response size: `4,874` bytes
- raw_response_id: ``
- model: `gpt-5.5`
- top keys: `brief, model, ok, raw_response_id, received_at, source, target_date, web_sources`
- `brief` keys: `false_leads, market_focus_summary, missing_assets, source_gaps, suggested_broadcast_order, what_market_is_watching`

| rank | use | focus | evidence_ids | host sentence |
| --- | --- | --- | --- | --- |
| 1 | lead | 인플레이션 재경계가 금리와 달러를 다시 시장의 발목으로 만드는가 | tradingview-com-news-064, finance-yahoo-com-source-010 | 오늘은 헤드라인보다 금리와 달러가 위험자산의 상단을 어디까지 누르는지부터 보겠습니다. |
| 2 | supporting_story | 이란/유가 헤드라인은 시장을 흔드는 원인인가, 말거리인가 | cnbc-com-world-040, https://x.com/KobeissiLetter/status/2050710022938558611 | 이란 뉴스는 크지만, 방송에서는 유가와 에너지주가 따라오는지를 먼저 따져보겠습니다. |
### Market Focus source gaps
- 전날 미국장 지수 종가와 섹터별 실제 반응

## 7. Editorial Brief API
- Input: Market Focus output + Market Radar candidates + recent briefs/feedback + visual/material candidates
- Model: `None`, fallback: `True`
- raw_response_id: ``
- daily_thesis: 에너지/지정학, 단신/화제 재료를 3개 묶어, 오늘 시장이 실제로 반응한 축인지 확인하는 꼭지입니다. 핵심 근거는 BREAKING: President Trump says he will be r…, TRUMP ON IRAN: MAYBE BETTER O…
- market_map_summary: fallback 결과입니다. 시장 지도는 지수/히트맵/금리/유가/달러/비트코인 차트에서 수동 확인하세요.
- storyline_count: `3`
- raw response: none

| rank | stars | title | hook | evidence_to_use | ppt_asset_queue labels |
| --- | --- | --- | --- | --- | --- |
| 1 | 3 | 이란 뉴스에 되살아난 유가 프리미엄 | 에너지/지정학, 단신/화제 재료를 3개 묶어, 오늘 시장이 실제로 반응한 축인지 확인하는 꼭지입니다. 핵심 근거는 BREAKING: President Trump says he will be r…, TRUMP ON IRAN: MAYBE BETTER OFF NOT MAKING…, Trump says there is poss… | https://x.com/KobeissiLetter/status/2050710022938558611, https://x.com/wallstengine/status/2050372648077865429, https://x.com/Reuters/status/2050774856640127425, finance-yahoo-com… | BREAKING: President Trump says he will be reviewing the plan that Iran has sent to the US but “can’t imagine that it wou, Trump says there is possibility US could restart strikes… |
| 2 | 3 | 이란 뉴스에 되살아난 유가 프리미엄 | 에너지/지정학, 금리/매크로 재료를 3개 묶어, 오늘 시장이 실제로 반응한 축인지 확인하는 꼭지입니다. 핵심 근거는 Vietnam’s inflation picked up more than exp…, WTI Oil Prices in Real Terms, US Jobs Report to Show Resilience in t… | https://x.com/business/status/2050770083039883365, isabelnet-com-blog-013, finance-yahoo-com-source-021 | Vietnam’s inflation picked up more than expected in April, as a surge in global energy prices driven by the Iran war beg, WTI Oil Prices in Real Terms, US Jobs Report to Show Resi… |
| 3 | 3 | 금리와 달러가 오늘의 숨은 제약인가 | 금리/매크로 재료를 3개 묶어, 오늘 시장이 실제로 반응한 축인지 확인하는 꼭지입니다. 핵심 근거는 The US government's cash balance is rising:…, Average 30-Year Mortgage Rate in the US… 19…, Recent inflation data was 'bad… | https://x.com/KobeissiLetter/status/2050722187884089775, https://x.com/charliebilello/status/2050598689849143303, https://x.com/Reuters/status/2050777376536101213, cnbc-com-world-… | The US government's cash balance is rising: The Treasury General Account (TGA) is up to ~$1 trillion, the highest since, Average 30-Year Mortgage Rate in the US… 1970s: 8.9% 1980s… |

## 8. Fixed Renderer: Visible vs Filtered
- Contract: LLM output supplies values only; renderer owns section names, order, and allowed public fields.
- Host area exposes exactly 3 news bullets, 5 broadcast-order bullets, and 3 storylines.
- Storyline rank >= 4, internal role/id/hash, and raw source metadata are filtered out of the publish host area.
- Collection area exposes only `## 1. 시장은 지금` and `## 2. 미디어 포커스`.
- Market material order is deterministic: index flow -> heatmaps -> rates -> oil -> dollar/FX -> risk assets -> FedWatch.
- Media focus cards follow storyline slide order and receive circled numbers.
### Host slide labels
- `① 유가 지정학 기사`
- `② WTI·브렌트 가격 차트`
- `③ 에너지주 반응 차트`
- `⑥ 금리 부담 기사`
- `⑦ Fed 인플레이션 발언 기사`
### Market-now cards
- count: `12`
| label | source | has_content | image_count |
| --- | --- | --- | --- |
| 주요 지수 흐름 | [finviz-index-futures](https://finviz.com/) |  | 2 |
| S&P500 히트맵 | [finviz-sp500-heatmap](https://finviz.com/map.ashx?t=sec) |  | 1 |
| 러셀 2000 히트맵 | [finviz-russell-heatmap](https://finviz.com/map?t=sec_rut) |  | 1 |
| 10년물 국채금리 | [Yahoo Finance](https://finance.yahoo.com/quote/%5ETNX) |  | 1 |
| WTI 가격 차트 | [Yahoo Finance](https://finance.yahoo.com/quote/CL%3DF) |  | 1 |
| 브렌트 가격 차트 | [Yahoo Finance](https://finance.yahoo.com/quote/BZ%3DF) |  | 1 |
| 달러인덱스 차트 | [Yahoo Finance](https://finance.yahoo.com/quote/DX-Y.NYB) |  | 1 |
| 원/달러 환율 차트 | [Yahoo Finance](https://finance.yahoo.com/quote/KRW%3DX) |  | 1 |
| 비트코인 가격 차트 | [CoinGecko](https://www.coingecko.com/en/coins/bitcoin) |  | 1 |
| CNN Fear & Greed | [cnn-fear-greed](https://edition.cnn.com/markets/fear-and-greed) |  | 1 |
| FedWatch 단기 금리 확률 | [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) |  | 1 |
| FedWatch 장기 금리 확률 | [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) |  | 1 |
### Media focus cards
- count: `13`
| label | source | has_content | image_count |
| --- | --- | --- | --- |
| ① 유가 지정학 기사 | [KobeissiLetter](https://x.com/KobeissiLetter/status/2050710022938558611) | True | 1 |
| ② WTI·브렌트 가격 차트 | [IsabelNet](https://www.isabelnet.com/the-cost-of-a-barrel-of-oil-in-real-u-s-dollar-terms) | True |  |
| ③ 에너지주 반응 차트 | Autopark | True |  |
| ④ 보강 후보 자료 | Market Focus | True |  |
| ⑤ 프리플라이트 보강 자료 | Pre-flight Agenda | True |  |
| ⑥ 금리 부담 기사 | [Charlie Bilello](https://x.com/charliebilello/status/2050598689849143303) | True | 1 |
| ⑦ Fed 인플레이션 발언 기사 | [Reuters](https://x.com/Reuters/status/2050777376536101213) | True | 1 |
| ⑧ XLE 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=XLE&p=d) | True | 1 |
| ⑨ CVX 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=CVX&p=d) | True | 1 |
| ⑩ XOM 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=XOM&p=d) | True | 1 |
| ⑪ GOOGL 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=GOOGL&p=d) | True | 1 |
| ⑫ MSFT 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=MSFT&p=d) | True | 1 |
| ⑬ META 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=META&p=d) | True | 1 |
### Renderer filter check
- source_role: `0`
- evidence_role: `0`
- item_id: `0`
- evidence_id: `0`
- asset_id: `0`
- MF-: `0`
- # PPT 제작 큐: `0`
- 자료 수집 상세: `0`
- Audit: `0`
- Debug: `0`

## 8.1 Dashboard Microcopy
- microcopy_enabled: `False`
- model: `gpt-5-mini`
- source: `deterministic`
- request_count: `0`
- card_count: `13`
- fallback_count: `16`
- invalid_output_count: `0`
- estimated_tokens: `2078`
- generated fields: `quote_lines, host_relevance_bullets, content_bullets`
### Microcopy storyline fields
| storyline_id | quote_lines | host_relevance_bullets |
| --- | --- | --- |
| storyline-1 | 유가 헤드라인과 실제 가격 반응이 같은 방향인지 먼저 분리한다. / 오늘은 헤드라인보다 금리와 달러가 위험자산의 상단을 어디까지 누르는지부터 보겠습니다. / 10년물, 달러인덱스, USD/KRW 차트가 주식 반응과 같은 방향인지 확인해야 한다. | 전일에도 비슷한 테마가 있어 감점했지만, 오늘 새 근거가 충분해 후보로 유지했습니다. / 첫 5분에는 뉴스 강도와 가격 반응의 차이를 보여주면 이해가 빠르다. / 같은 주식 호재라도 금리와 달러가 버티면 밸류에이션이 높은 기술주와 한국장 성장주에는 부담으로 번질 수 있다. |
| storyline-3 | 유가 헤드라인과 실제 가격 반응이 같은 방향인지 먼저 분리한다. / 이란 뉴스는 크지만, 방송에서는 유가와 에너지주가 따라오는지를 먼저 따져보겠습니다. / WTI/Brent와 XLE 반응이 함께 움직이는지 확인해야 한다. | 지정학 뉴스 반복이 유가와 에너지주 가격 반응으로 확인되는가? / 유가가 따라오지 않으면 지정학 뉴스는 첫 꼭지보다 리스크 체크용 보조 꼭지에 가깝다. / 한국장에서는 정유·화학·항공과 물가 부담 장표로 곧장 이어진다. |
| storyline-2 | 금리와 달러가 위험자산 반등의 속도를 다시 제한하는지 확인한다. / 전일 고정 프레임보다 오늘 수집물의 점수와 구체성이 더 강하게 잡힌 묶음입니다. / 지수보다 채권·환율 반응을 먼저 봐야 하는 아침이다. | 전일 고정 프레임보다 오늘 수집물의 점수와 구체성이 더 강하게 잡힌 묶음입니다. / 첫 5분에는 지수보다 10년물·달러 흐름을 먼저 보여주는 편이 빠르다. / 한국장에서는 환율과 성장주 밸류에이션 부담으로 바로 연결된다. |
### Microcopy media fields
| card_key | content_bullets |
| --- | --- |
| media_focus:https:-x.com-KobeissiLetter-status-2050710022938558611 | 유가와 지정학 리스크 관련 내용입니다. / 유가 지정학 기사 / 유가 지정학 기사의 시장 반응과 방송 연결 포인트를 확인한다. |
| media_focus:isabelnet-com-blog-013 | 유가와 지정학 리스크 관련 내용입니다. / WTI·브렌트 가격 차트 / WTI·브렌트 가격 차트의 시장 반응과 방송 연결 포인트를 확인한다. |
| media_focus:15:에너지주-반응-차트 | 에너지주 반응 차트 / 에너지주 반응 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 유가 헤드라인이 실제 가격과 에너지주 반응으로 이어지는지 보는 자료다. |
| media_focus:16:보강-후보-자료 | 전날 미국장 지수 종가와 섹터별 실제 반응 / 보강 후보 자료 / 보강 후보 자료의 시장 반응과 방송 연결 포인트를 확인한다. |
| media_focus:17:프리플라이트-보강-자료 | 발견 힌트상 주식은 강하지만 채권시장은 인플레·유가·Fed 경로를 더 경계할 수 있음. / 한국 개인투자자에게 환율과 성장주 할인율이 1차 체크포인트. / 미 10년물·DXY·USD/KRW가 주식 사상권 랠리를 제약하는가, 아니면 위험선호를 확인하는가? |
| media_focus:https:-x.com-charliebilello-status-2050598689849143303 | 연준과 인플레이션 경로를 보는 자료입니다. / 금리 부담 기사 / 금리 부담 기사의 시장 반응과 방송 연결 포인트를 확인한다. |
| media_focus:https:-x.com-Reuters-status-2050777376536101213 | 연준과 인플레이션 경로를 보는 자료입니다. / Fed 인플레이션 발언 기사 / Fed 인플레이션 발언 기사의 시장 반응과 방송 연결 포인트를 확인한다. |
| media_focus:XLE | XLE 일간 차트 / XLE 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 유가 헤드라인이 실제 가격과 에너지주 반응으로 이어지는지 보는 자료다. |
| media_focus:CVX | CVX 일간 차트 / CVX 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 유가 헤드라인이 실제 가격과 에너지주 반응으로 이어지는지 보는 자료다. |
| media_focus:XOM | XOM 일간 차트 / XOM 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 유가 헤드라인이 실제 가격과 에너지주 반응으로 이어지는지 보는 자료다. |
| media_focus:GOOGL | GOOGL 일간 차트 / GOOGL 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 기술주 반응을 AI·실적 기대와 분리해 확인하는 보조 자료다. |
| media_focus:MSFT | MSFT 일간 차트 / MSFT 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 기술주 반응을 AI·실적 기대와 분리해 확인하는 보조 자료다. |
| media_focus:META | META 일간 차트 / META 일간 차트의 시장 반응과 방송 연결 포인트를 확인한다. / 기술주 반응을 AI·실적 기대와 분리해 확인하는 보조 자료다. |

## 9. Quality Gate
- gate: `pass`
- format_score: `100`
- content_score: `100`
- integrity_score: `100`
- finding_count: `0`
- findings: none

## 10. Reproduction / Trace Files
- projects\autopark\data\processed\2026-05-03\market-preflight-agenda.json
- projects\autopark\data\processed\2026-05-03\today-misc-batch-a-candidates.json
- projects\autopark\data\processed\2026-05-03\today-misc-batch-b-candidates.json
- projects\autopark\data\processed\2026-05-03\x-timeline-posts.json
- projects\autopark\data\processed\2026-05-03\visual-cards.json
- projects\autopark\data\processed\2026-05-03\market-radar.json
- projects\autopark\data\processed\2026-05-03\market-focus-brief.json
- projects\autopark\data\processed\2026-05-03\editorial-brief.json
- projects\autopark\runtime\notion\2026-05-03\26.05.03.md
- projects\autopark\runtime\reviews\2026-05-03\dashboard-quality.json
