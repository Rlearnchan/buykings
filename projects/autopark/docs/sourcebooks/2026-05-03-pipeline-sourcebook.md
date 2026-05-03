# 26.05.03 Autopark Pipeline Sourcebook

- Generated at: `26.05.03 18:33`
- Scope: end-to-end sourcebook for the compact dashboard pipeline: collection, API reasoning, filtering, renderer decisions, and quality gate.
- Hygiene: credentials, browser/session data, signed URLs, raw HTML, full article bodies, and full X text are not included.
- Long source material is represented as title/source/role/URL/summary only.

## 0. Artifact Inventory
- `projects\autopark\data\processed\2026-05-03\earnings-calendar-tickers.json` (29,821 bytes)
- `projects\autopark\data\processed\2026-05-03\earnings-calendar-x-posts.json` (9,581 bytes)
- `projects\autopark\data\processed\2026-05-03\earnings-ticker-drilldown.json` (78,234 bytes)
- `projects\autopark\data\processed\2026-05-03\economic-calendar.json` (300 bytes)
- `projects\autopark\data\processed\2026-05-03\editorial-brief.json` (44,463 bytes)
- `projects\autopark\data\processed\2026-05-03\finviz-feature-stocks.json` (28,258 bytes)
- `projects\autopark\data\processed\2026-05-03\market-focus-brief.json` (17,435 bytes)
- `projects\autopark\data\processed\2026-05-03\market-preflight-agenda.json` (27,887 bytes)
- `projects\autopark\data\processed\2026-05-03\market-radar.json` (273,677 bytes)
- `projects\autopark\data\processed\2026-05-03\today-misc-batch-a-candidates.json` (70,070 bytes)
- `projects\autopark\data\processed\2026-05-03\today-misc-batch-b-candidates.json` (16,075 bytes)
- `projects\autopark\data\processed\2026-05-03\visual-cards.json` (9,035 bytes)
- `projects\autopark\data\processed\2026-05-03\x-timeline-posts.json` (130,985 bytes)
- `projects\autopark\runtime\notion\2026-05-03\26.05.03.md` (11,273 bytes)

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
- Public-use guard: `[{'reason': 'pre-flight 단계에는 local evidence_id가 없고 검증 패킷이 생성되지 않았다.', 'rule': '이 JSON의 어떤 문장도 방송 멘트나 공개 대시보드 근거로 직접 사용 금지.'}, {'reason': '웹 검색은 발견용이며 원문·차트·로컬 캡처로 재검증해야 한다.', 'rule': '뉴스 검색 결과를 인과관계 증거로 사용 금지.'}, {'reason': 'X/social은 심리 확인용이며 대표성·정확성이 없다.', 'rule': 'X 검색 결과를 사실 근거 또는 가격 원인으로 사용 금지.'}, {'reason': '차트는 시장 반응을 보여줄 뿐 원인을 증명하지 않는다.', 'rule': '차트만으로 ‘때문에 올랐다/내렸다’ 단정 금지.'}]`
- agenda_items: `8`
- collection_priorities: `4`
- raw response path: `projects\autopark\runtime\openai-responses\2026-05-03-market-preflight-raw.json`
- raw response size: `28,677` bytes
- raw_response_id: `resp_0e5c6c02ece5ee1d0069f6e40779008195b5a3834a6d69b0ef`
- model: `gpt-5.5`
- top keys: `agenda, model, raw_response_id, source, web_sources`
- `agenda` keys: `agenda_items, collection_priorities, date, do_not_use_publicly, preflight_summary, source_gaps_to_watch`

| rank | agenda_id | market_question | collection_targets | why_to_check |
| --- | --- | --- | --- | --- |
| 1 | agenda_equity_breadth | S&P500·Nasdaq 신고가 흐름이 대형 기술주 집중 랠리인지, 시장 전반 확산인지 확인할 것인가? | chart:S&P500, Nasdaq, Dow, Russell2000, S&P500 Equal We…; market_reaction:May 1 2026 US market close sector performance XLK…; capture:미국장 마감 히트맵: mega-cap tech vs cyclicals vs def… | 금요일 미국장 이후 한국 개인투자자에게 첫 화면은 지수 방향보다 폭과 질이 중요하다. |
| 2 | agenda_rates_dollar | 최근 주가 랠리가 장기금리 안정과 달러 약세를 동반했는지, 아니면 금리 부담을 무시한 리스크온인지 확인할 것인가? | chart:US10Y, US2Y, 2s10s, DXY, USD/KRW, USD/JPY: Apr 29…; official_source:Federal Reserve April 29 2026 FOMC statement and…; market_reaction:Fed funds futures implied cuts 2026 af… | 한국 투자자에게 미국 10년물, DXY, USD/KRW는 나스닥과 반도체 밸류에이션의 핵심 필터다. |
| 3 | agenda_ai_capex | 빅테크 AI CAPEX 확대가 ‘수요 확인’으로 매수되는지, ‘마진 훼손’으로 할인되는지 종목별로 갈렸는가? | chart:MSFT AMZN GOOGL META NVDA AVGO AMD MU: earnings 이…; official_source:Microsoft Alphabet Meta Amazon Q1 2026 earnings r…; news_search:Q1 2026 big tech AI capex guidance Micros… | AI 인프라 지출은 미국 빅테크, 엔비디아, 한국 HBM·장비주를 동시에 움직이는 핵심 축이다. |
| 4 | agenda_semis_hbm_korea | 미국 AI 인프라 지출이 엔비디아·브로드컴·마이크론뿐 아니라 삼성전자·SK하이닉스·한국 장비주로 연결되는가? | chart:NVDA AVGO AMD MU SMH SOXX vs Samsung Electronics…; official_source:Samsung Electronics SK hynix Q1 2026 earnings rel…; news_search:May 2026 Samsung SK hynix HBM shortage AI… | 방송 시청자 포트폴리오와 직접 연결되는 반도체·HBM 수혜 확인 항목이다. |
| 5 | agenda_oil_risk | 유가 하락 또는 안정이 인플레이션 안도 요인인지, OPEC+·재고·지정학 리스크가 남아 있는지 확인할 것인가? | chart:WTI front month, Brent front month, Brent-WTI spr…; official_source:EIA Weekly Petroleum Status Report week ended Apr…; news_search:May 2 2026 OPEC+ June output target incre… | 유가는 미국 인플레 기대, 항공·화학·정유, 한국 무역수지와 원화에 동시에 영향을 준다. |
| 6 | agenda_jobs_inflation | 이번 주 미국 고용·물가 캘린더가 주식 랠리를 뒷받침할 ‘골디락스’인지, 금리 재상승 리스크인지 확인할 것인가? | official_source:BLS Employment Situation April 2026 release sched…; official_source:BEA March 2026 PCE price index release April 30 2…; chart:Core PCE YoY/MoM, CPI YoY/MoM, averag… | 5월 초 방송에서는 지난 PCE와 다음 고용지표를 연결해 금리 민감도를 점검해야 한다. |
| 7 | agenda_fx_korea | 달러/원은 미국 금리·DXY보다 유가와 한국 반도체 수출 호조에 더 민감하게 움직였는가? | chart:USD/KRW, DXY, US10Y, WTI, KOSPI, KOSDAQ, foreign…; official_source:Bank of Korea daily FX rate USD/KRW and market co…; official_source:Korea April 2026 exports imports trade… | 한국 개인투자자의 미국주식 환차손익과 국내 증시 외국인 수급에 직접 연결된다. |
| 8 | agenda_bitcoin_risk | 비트코인이 나스닥·달러·금리와 같은 방향으로 움직여 위험선호 확인 지표로 쓸 수 있는가? | chart:Bitcoin spot, Nasdaq futures, DXY, US10Y: May 1 c…; market_reaction:BTC vs QQQ vs DXY correlation last 30 days and we…; news_search:Bitcoin May 2026 weekend move Nasdaq doll… | 한국 개인투자자 관심도가 높고, 주말 장중에도 움직여 월요일 아침 리스크온 확인에 유용하다. |

## 3. News / X / Earnings Collection
### News batch A
- captured_at: `2026-05-03T14:59:52+09:00`
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
| 6 | 2 days ago TradingView AMZN: Amazon Stock Jumps After Earnings, Revenue Top Consensus Estimates | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/tradingview:2532cf758094b:0-amzn-amazon-stock-jumps-after-earnings-revenue-top-consensus-estimates |
| 7 | 2 days ago TradingView MSFT: Microsoft Stock Steady After Strong Earnings, Cloud Growth Hits 40% | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/tradingview:f337d69c7094b:0-msft-microsoft-stock-steady-after-strong-earnings-cloud-growth-hits-40 |
| 8 | Apr 23 TradingView IBM Stock Sheds 7% Despite Double Beat. It’s the Disappointing Guidance. | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/tradingview:814d16f2a094b:0-ibm-stock-sheds-7-despite-double-beat-it-s-the-disappointing-guidance |
| 9 | Apr 23 TradingView TSLA: Tesla Stock Slides After Tiny Revenue Miss, High Capex. Profit Soars 136%. | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/tradingview:4305c607d094b:0-tsla-tesla-stock-slides-after-tiny-revenue-miss-high-capex-profit-soars-136 |
| 10 | Apr 24 TradingView INTC: Intel Stock Up Massive 20% After Earnings Crush Estimates | Financial News & Top Stories — Market Analysis — TradingView |  | https://www.tradingview.com/news/tradingview:e948c25f2094b:0-intc-intel-stock-up-massive-20-after-earnings-crush-estimates |

### News batch B
- captured_at: `2026-05-03T14:59:57+09:00`
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
- captured_at: `2026-05-03T06:00:10.872Z`
- lookback_hours: `48`
- require_recent_signal: `None`
- collected_count: `84`

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
- screenshots: `5` under `projects\autopark\runtime\screenshots\2026-05-03`
- chart exports: `10` under `projects\autopark\exports\current`
| kind | file |
| --- | --- |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\cnn-fear-greed-gauge.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-index-futures-1.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-index-futures-2.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-russell-heatmap-map.png |
| screenshot | projects\autopark\runtime\screenshots\2026-05-03\finviz-sp500-heatmap-map.png |
| chart | projects\autopark\exports\current\bitcoin.png |
| chart | projects\autopark\exports\current\crude-oil-brent.png |
| chart | projects\autopark\exports\current\crude-oil-wti.png |
| chart | projects\autopark\exports\current\dollar-index.png |
| chart | projects\autopark\exports\current\economic-calendar-global.png |
| chart | projects\autopark\exports\current\economic-calendar-us.png |
| chart | projects\autopark\exports\current\fedwatch-conditional-probabilities-long-term.png |
| chart | projects\autopark\exports\current\fedwatch-conditional-probabilities-short-term.png |
| chart | projects\autopark\exports\current\us10y.png |
| chart | projects\autopark\exports\current\usd-krw.png |

## 5. Market Radar Merge / Selection
- generated_at: `2026-05-03T15:05:12`
- candidate_count: `124`
- storylines in radar: `5`
- Internal role/id fields remain available for audit, but are not rendered in publish Markdown.
| id | title | source | source_role | evidence_role |
| --- | --- | --- | --- | --- |
| https://x.com/KobeissiLetter/status/2050710022938558611 | BREAKING: President Trump says he will be reviewing the plan that Iran has sent to the US but “can’t imagine that it wou | (13) The Kobeissi Letter (@KobeissiLetter) / X | sentiment_probe | sentiment |
| https://x.com/wallstengine/status/2050376010269634723 | Apple raised the Mac mini’s starting price to $799 from $599 after AI demand and chip supply constraints drained invento | (16) Wall St Engine (@wallstengine) / X | sentiment_probe | sentiment |
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
| https://x.com/business/status/2050740844563493368 | Australian Prime Minister Anthony Albanese said the coming budget will boost spending on Medicare urgent care clinics as | Bloomberg (@business) / X | sentiment_probe | sentiment |

## 6. Market Focus Brief API
- Input: market-radar/local candidates + preflight agenda + sanitized local packet
- Model: `gpt-5.5`, fallback: `False`, with_web: `False`
- focus_count: `4`
- source_gap_count: `5`
- raw_response_id: `resp_007ce719a952f8390069f6e7018cbc81959b96255199fd7642`
### Sanitized prompt check
- prompt check file: missing
- raw response path: `projects\autopark\runtime\openai-responses\2026-05-03-market-focus-raw.json`
- raw response size: `16,281` bytes
- raw_response_id: `resp_007ce719a952f8390069f6e7018cbc81959b96255199fd7642`
- model: `gpt-5.5`
- top keys: `brief, model, ok, raw_response_id, received_at, source, target_date, web_sources`
- `brief` keys: `false_leads, market_focus_summary, missing_assets, source_gaps, suggested_broadcast_order, what_market_is_watching`

| rank | use | focus | evidence_ids | host sentence |
| --- | --- | --- | --- | --- |
| 1 | lead | 유가·이란 프리미엄이 다시 인플레와 위험선호를 흔드는가 | cnbc-com-world-051, finance-yahoo-com-source-018, finance-yahoo-com-source-016, https://x.com/Reuters/status/2050810107324211286, https://x.com/Reuters/status/2050774856640127425,… | 오늘 미국장 해석의 출발점은 이란 뉴스 자체가 아니라, 100달러대 유가가 인플레와 Fed 기대를 다시 압박하느냐입니다. |
| 2 | supporting_story | 빅테크 실적이 랠리의 방어 논리인가, 종목별 선별 장세인가 | cnbc-com-world-053, cnbc-com-world-026, cnbc-com-world-035, tradingview-com-news-009, tradingview-com-news-008, tradingview-com-news-002, insight-factset-com-source-002, https://x… | 유가가 매크로 부담이라면, 이를 버티게 한 쪽은 빅테크 실적과 클라우드 성장 기대였습니다. |
| 3 | supporting_story | 금리·달러는 랠리의 제약인가, 아직은 통제 가능한 변수인가 | finance-yahoo-com-source-010, https://x.com/Reuters/status/2050777376536101213, cnbc-com-world-030, https://x.com/LizAnnSonders/status/2050225388928795107, https://x.com/LizAnnSon… | 10년물은 조금 내려왔지만, 시장은 이번 주 고용과 물가성 지표가 다시 금리 경로를 흔들지 확인하려 합니다. |
| 4 | talk_only | AI 인프라 수요가 한국 반도체로 연결되는가 | https://x.com/business/status/2050740299614335408, https://x.com/business/status/2050771436868944114, tradingview-com-news-008, tradingview-com-news-009 | AI 인프라 기대가 한국 반도체로 이어지는지는 중요하지만, 오늘 패킷만으로는 말로 짚고 데이터는 추가 확인해야 합니다. |
### Market Focus source gaps
- 미국 지수 랠리의 폭과 질 확인 자료 부족
- 유가 뉴스의 공식·원문 검증 부족
- Fed 기대 변화 수치 부재
- 빅테크 AI CAPEX 원문 검증 부족
- 한국 반도체 연결고리의 로컬 가격·공식 자료 부족

## 7. Editorial Brief API
- Input: Market Focus output + Market Radar candidates + recent briefs/feedback + visual/material candidates
- Model: `gpt-5-mini`, fallback: `False`
- raw_response_id: `resp_073ba6c1e3cf0f0e0069f6ead568e08195b64f3489f5511c48`
- daily_thesis: 오늘 미국장 핵심은 ‘유가가 다시 100달러대라는 점이 인플레이션·Fed 경로에 얼마나 부담을 주느냐’다. 그 부담을 일정 부분 흡수한 동력은 빅테크 실적의 선별적 강세이고, 금리·달러 변동은 랠리를 제약할 가능성이 남아 있다.
- market_map_summary: 미국 장 마감·지수 히트맵과 종목별 반응은 ‘에너지·몇몇 대형 기술주 간 차별적 흐름’을 보여준다. 에너지 섹터(오일) 관련 불확실성은 남아있지만 장중 유가는 하락 전환해 ‘급등’보다는 ‘높게 유지되는 유가가 남긴 인플레 부담’으로 해석하는 게 적절하다.
- storyline_count: `4`
### debug_stats.first_attempt
- model: `gpt-5-mini`
- timeout_seconds: `120`
- request_started_at: `2026-05-03T15:27:32+09:00`
- request_finished_at: `2026-05-03T15:29:27+09:00`
- elapsed_seconds: `114.703`
- candidate_count_total: `124`
- candidate_count_sent: `56`
- market_focus_available: `True`
- market_focus_focus_count: `4`
- market_focus_source_gap_count: `5`
- prompt_chars: `150968`
- estimated_prompt_tokens: `37742`
- max_output_tokens: `16384`
- raw_response_id: `resp_073ba6c1e3cf0f0e0069f6ead568e08195b64f3489f5511c48`
- raw response path: `projects\autopark\runtime\openai-responses\2026-05-03-editorial-raw.json`
- raw response size: `41,235` bytes
- raw_response_id: `resp_073ba6c1e3cf0f0e0069f6ead568e08195b64f3489f5511c48`
- model: `gpt-5-mini`
- top keys: `brief, model, ok, raw_response_id, received_at, source, target_date`
- `brief` keys: `broadcast_mode, daily_thesis, drop_list, editorial_summary, market_map_summary, one_line_market_frame, ppt_asset_queue, retrospective_watchpoints, storylines, talk_only_queue`

| rank | stars | title | hook | evidence_to_use | ppt_asset_queue labels |
| --- | --- | --- | --- | --- | --- |
| 1 | 3 | 유가 100달러대 — 인플레·Fed 기대를 다시 흔드는가 | 유가가 다시 100달러대입니다. 오늘 시장의 출발점은 ‘이 지정학 뉴스가 단순 헤드라인이 아니라 인플레이션·금리 경로를 다시 압박하느냐’입니다. | isabelnet-com-blog-013, finance-yahoo-com-source-016, cnbc-com-world-051, https://x.com/Reuters/status/2050774856640127425, https://x.com/KobeissiLetter/status/2050710022938558611 | WTI Oil Prices in Real Terms, US Jobs Report to Show Resilience in the Wake of Iran War (Yahoo), Exxon Mobil CEO expects higher oil prices due to Iran war (CNBC), Trump says there… |
| 2 | 2 | 빅테크 실적 — 모두가 오른 게 아니라 선별됐다 | 유가(인플레)가 부담이라면, 그 부담을 일부 흡수한 것은 빅테크의 실적 선별성입니다. | insight-factset-com-source-002, cnbc-com-world-053, tradingview-com-news-009, tradingview-com-news-008, https://x.com/bespokeinvest/status/2050286082734932276 | S&P 500 Earnings Season Update: May 1, 2026 (FactSet), The market isn't grading all Big Tech earnings the same (CNBC), MSFT 일간 차트 (Finviz), AMZN 일간 차트 (Finviz) |
| 3 | 2 | 금리는 내려도 안심 못하는 이유: 달러·물가·유동성 변수 | 10년물은 소폭 하락했지만, Fed 발언과 달러·물가 지표는 여전히 시장을 불안하게 한다. | finance-yahoo-com-source-010, https://x.com/Reuters/status/2050777376536101213, https://x.com/KobeissiLetter/status/2050722187884089775, https://x.com/LizAnnSonders/status/2050225… | The US government's cash balance is rising: TGA ≈ $1tn (Kobeissi Letter), Recent inflation data was 'bad news,' Fed's Goolsbee says (Reuters X) |
| 4 | 1 | AI 인프라 기대와 한국 반도체 연결고리(말로 짚기) | AI 인프라가 한국 반도체로 이어질까? 오늘은 ‘확인 필요’라는 결론입니다. | https://x.com/business/status/2050740299614335408, tradingview-com-news-009, tradingview-com-news-008, cnbc-com-world-030, insight-factset-com-source-002 | The list of Asian stocks that benefit from business partnership with Nvidia is getting longer, as the region further int, 2 days ago TradingView AMZN: Amazon Stock Jumps After Ear… |

## 8. Fixed Renderer: Visible vs Filtered
- Contract: LLM output supplies values only; renderer owns section names, order, and allowed public fields.
- Host area exposes exactly 3 news bullets, 5 broadcast-order bullets, and 3 storylines.
- Storyline rank >= 4, internal role/id/hash, and raw source metadata are filtered out of the publish host area.
- Collection area exposes only `## 1. 시장은 지금` and `## 2. 미디어 포커스`.
- Market material order is deterministic: index flow -> heatmaps -> rates -> oil -> dollar/FX -> risk assets -> FedWatch.
- Media focus cards follow storyline slide order and receive circled numbers.
### Host slide labels
- `① WTI·브렌트 가격 차트`
- `② 유가 지정학 기사`
- `③ 에너지주 반응 차트`
- `④ FactSet 실적 시즌 요약`
- `⑤ 빅테크 실적 반응 자료`
- `⑥ 실적 특징주 차트`
- `⑦ 10년물 국채금리`
- `⑧ Fed 인플레이션 발언 기사`
- `⑨ 금리 부담 기사`
### Market-now cards
- count: `11`
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
| FedWatch 금리 확률 | [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) |  | 2 |
### Media focus cards
- count: `16`
| label | source | has_content | image_count |
| --- | --- | --- | --- |
| ① WTI·브렌트 가격 차트 | [IsabelNet](https://www.isabelnet.com/the-cost-of-a-barrel-of-oil-in-real-u-s-dollar-terms) | True |  |
| ② 유가 지정학 기사 | [Yahoo Finance](https://finance.yahoo.com/news/us-jobs-report-show-resilience-200000920.html) | True |  |
| ③ 에너지주 반응 차트 | Autopark | True |  |
| ④ 보강 후보 자료 | Market Focus | True |  |
| ⑤ 프리플라이트 보강 자료 | Pre-flight Agenda | True |  |
| ⑥ FactSet 실적 시즌 요약 | [FactSet Insight - Comme…](https://insight.factset.com/sp-500-earnings-season-update-may-1-2026) | True |  |
| ⑦ 빅테크 실적 반응 자료 | [CNBC](https://www.cnbc.com/2026/05/01/apple-stock-rallies-on-q2-earnings-and-q3-guidance.html) | True |  |
| ⑧ 실적 특징주 차트 | Autopark | True |  |
| ⑨ Fed 인플레이션 발언 기사 | [Yahoo Finance](https://finance.yahoo.com/economy/policy/articles/recent-inflation-data-bad-news-190611607.html) | True |  |
| ⑩ 금리 부담 기사 | [(16) Liz Ann Sonders (@…](https://x.com/LizAnnSonders/status/2050225388928795107) | True | 1 |
| ⑪ XLE 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=XLE&p=d) | True | 1 |
| ⑫ CVX 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=CVX&p=d) | True | 1 |
| ⑬ XOM 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=XOM&p=d) | True | 1 |
| ⑭ GOOGL 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=GOOGL&p=d) | True | 1 |
| ⑮ MSFT 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=MSFT&p=d) | True | 1 |
| ⑯ META 일간 차트 | [Finviz](https://finviz.com/quote.ashx?t=META&p=d) | True | 1 |
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
