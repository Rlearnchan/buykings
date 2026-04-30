# Autopark Source Intelligence Map

이 문서는 Autopark가 아침방송 대시보드를 만들 때 각 소스에서 무엇을 얻을 수 있는지 정리한 1차 리서치 맵이다.

작성 기준:

- 로컬 근거: `projects/autopark/sources.xlsx`, `projects/autopark/config/today_misc_sources.json`, `projects/autopark/data/processed/2026-04-30/*`
- 웹 근거: 각 서비스의 공개 페이지/공식 설명/현재 사이트 구조
- 목적: 모든 소스를 많이 긁는 것이 아니라, 방송 제작자가 실제로 쓸 만한 자료를 어디서 얻는지 역할을 나누는 것

## Executive Takeaways

- **속보/당일 헤드라인**은 Reuters, Bloomberg, CNBC, Yahoo Finance, TradingView가 맡는다.
- **시장 데이터/고정 차트**는 Yahoo Finance, Trading Economics, CoinGecko, CNN Fear & Greed, CME FedWatch, Finviz가 맡는다.
- **시각자료/거시 차트**는 IsabelNet, Bespoke, Charlie Bilello, KobeissiLetter, StockMarket.News가 강하다.
- **실적 캘린더**는 Earnings Whispers가 가장 빠르고 시각적으로 좋다.
- **실적 시즌의 정량 맥락**은 FactSet Insight가 가장 안정적이다.
- **X 계정**은 단독 정보원이라기보다 "오늘 시장이 어떤 단어를 반복하는지" 보는 레이더로 쓰는 것이 좋다.

## Source Role Table

| 소스 | 주로 얻는 데이터 | 방송 활용 | 강점 | 약점/주의 | 자동화 우선순위 |
|---|---|---|---|---|---|
| Finviz | 지수 흐름, S&P500/러셀 히트맵, 티커 일봉, 티커별 뉴스 | `시장은 지금`, `특징주 분석` | 화면 자체가 방송용으로 직관적. 티커별 hot news가 출발점으로 좋음 | Cloudflare/headless 차단. persistent Chrome 필요 | P0 |
| Yahoo Finance | 지표/선물/환율/티커 가격, 일반 금융뉴스 | Datawrapper 시장지표, 보조 뉴스 | 무료 chart endpoint로 시계열 수집이 쉬움. 주식/ETF/환율/선물 커버 넓음 | 공식 API가 아님. limit/변경 리스크 있음 | P0 |
| Trading Economics | 경제 일정, 예상/이전/실제, 국가/중요도 | 경제 일정 표 | 경제캘린더가 구조화되어 있고 국가/중요도 필터 가능 | HTML 파싱은 변경 리스크. 유료 API 고려 가능 | P0 |
| CNN Fear & Greed | 투자심리 게이지 | `시장은 지금` 심리 체크 | 한 장으로 위험선호를 설명하기 좋음 | 캡처 의존. 세부 구성요소까지 자동 수집은 후속 | P0 |
| CME FedWatch | FOMC 회의별 금리확률, 전일/전주/전월 비교 | 금리/Fed 꼭지 | Fed funds futures 기반 확률이라는 명확한 해석 가능 | 페이지 구조 복잡. 캡처 자동화 필요 | P1 |
| Earnings Whispers | 주간/월간 실적 캘린더 이미지, 티커 리스트 | 실적 캘린더, 특징주 후보 seed | X 이미지가 바로 방송 자료로 좋고 OCR/티커 추출 가능 | 주간 캘린더 고정 포스트 타이밍 확인 필요 | P0 |
| FactSet Insight | S&P500 실적 시즌 업데이트, EPS/매출/마진/섹터 분석 | 실적 시즌 큰 맥락 | John Butters의 정량 실적 리포트가 강함 | 속보성은 낮고 기사 길이가 있음 | P1 |
| IsabelNet | 리서치 하우스/IB chart, valuation, sentiment, recession, positioning | 이모저모 시각자료 | 한 장짜리 차트가 방송용 자료로 매우 좋음 | 이미지 맥락을 해석해야 함. 원 출처/시점 확인 필요 | P0 |
| Reuters | 글로벌 속보, 정책/지정학/기업/시장 뉴스 | 메인 뉴스 후보, 단신 | 신뢰도와 속도. 글로벌 커버리지 | 사이트 직접 수집은 차단/페이월 가능. X 공개 헤드라인이 현실적 | P0 |
| Bloomberg | 금융시장/정책/기업/기술/문화의 money angle | 메인 스토리/단신 | 금융시장 관점과 데이터 그래픽/비디오가 강함 | paywall. 공개 X 헤드라인+이미지 우선 | P0 |
| CNBC | 미국 주식/빅테크/실적/Fed/에너지 기사 | 미국 시장 메인 뉴스, 종목 이슈 | 방송 톤과 잘 맞고 기사 제목이 직관적 | CNBC Pro와 일반 기사 분리 필요 | P0 |
| TradingView News | 시장 뉴스 aggregation, 티커/지수/섹터 반응 | 뉴스 후보 pool | 하루치 후보를 넓게 가져오기 쉬움 | 중복/평면적 기사 많음. 선별 점수 필요 | P1 |
| Advisor Perspectives | 장문 거시/자산배분 코멘터리, dshort/AP charts | 배경 설명, 주간/월간 맥락 | 퀄리티 좋은 장문 commentary와 지표 해설 | 매일 아침 속보용은 아님. 403 이슈 있음 | P2 |
| Bespoke | 시장 breadth, seasonality, performance, positioning chart | 이모저모/시장 내부 구조 | 짧고 읽기 쉬운 차트/코멘트 | 상당 부분 유료/로그인 가능성 | P1 |
| KobeissiLetter | 거시/정책/시장 stress, X 기반 시각자료/숫자 | 메인 thesis 후보, 키워드 레이더 | X에서 시장이 반응하는 숫자를 잘 뽑음 | 계정 성격상 과장/선별 편향 점검 필요 | P0 |
| Wall St Engine | 실적/기업 발언/AI/빅테크 X 속보 | 빅테크 실적, AI 스토리 | 짧은 quote와 숫자가 빠름 | X 로그인/정렬 이슈. 원문 교차검증 필요 | P0 |
| Charlie Bilello | 장기 차트, 자산별 수익률, 인플레/금리/시장 통계 | 이모저모 시각자료 | 설명이 짧고 차트가 방송용으로 좋음 | 개별 당일 뉴스보다는 통계/맥락형 | P1 |
| StockMarket.News / _Investinq | 화제성 있는 시장 영상/차트/quote | 단신/환기 소재, 흥미 유발 | 시각자료와 “볼 만한 소재”가 많음 | 검증/원출처 확인 필수 | P1 |
| Liz Ann Sonders | Schwab 관점의 시장/경제 차트 | 거시/시장 내부 구조 | 신뢰도 높은 차트와 코멘트 | 직접 원자료까지 확인하면 더 좋음 | P1 |
| Nick Timiraos | Fed 관련 해석/신호 | Fed 주간/회의 전후 핵심 | Fed watcher로서 가치 높음 | 모든 날에 자료가 있는 것은 아님 | P1 |

## 현재 Autopark에서 확인된 0430 수집 성과

### Batch A 뉴스

- CNBC, Yahoo Finance, TradingView는 정상 수집.
- Reuters 웹 직접 수집은 실패했지만 X 공개 헤드라인에서는 수집 가능.
- 후보 수는 TradingView 15, CNBC 15, Yahoo Finance 14로 넓게 들어왔다.
- 문제는 후보가 넓은 만큼 평면적 기사도 많다는 점이다.

### Batch B 특수/리서치

- IsabelNet은 이미지/차트 후보가 안정적으로 들어왔다.
- FactSet Insight는 source check는 성공했지만 0430 후보 장부에는 크게 반영되지 않았다.
- Advisor Perspectives는 403으로 실패했다.
- X 계정들은 수집 성공했지만, Batch B HTML 후보에서는 IsabelNet 비중이 압도적이었다.

### X Timeline

- Reuters, Bloomberg, CNBC, Wall St Engine, KobeissiLetter, Charlie Bilello, Liz Ann Sonders, Bespoke 등이 정상 수집됐다.
- 0430에서 CNBC의 UAE/OPEC, Bloomberg의 AI/Mercor·이란 유조선, Wall St Engine의 GOOGL TPU, Charlie Bilello의 유가/원자재 차트가 실질적으로 유용했다.
- X는 headline + image + 반응 지표를 주지만, 원문 기사/원출처 검증을 붙여야 한다.

### 실적/특징주

- Earnings Whispers X 캘린더는 주간 티커 seed로 매우 좋았다.
- Finviz는 일봉 + 티커 아래 hot news 한 줄 + 뉴스 테이블을 얻을 수 있어 특징주 출발점으로 적합했다.
- FactSet은 실적 시즌 큰 숫자와 섹터별 EPS/margin context를 보강하는 역할이 좋다.

## Recommended Source Tiers

### Tier 0: 매일 고정 수집

- Finviz
- Yahoo Finance
- Trading Economics
- CNN Fear & Greed
- Earnings Whispers
- Reuters X
- Bloomberg X
- CNBC X/웹
- Wall St Engine
- KobeissiLetter
- IsabelNet

### Tier 1: 조건부/주 2-3회 수집

- FactSet Insight
- Bespoke
- Charlie Bilello
- Liz Ann Sonders
- Nick Timiraos
- TradingView News
- Advisor Perspectives

### Tier 2: 후보 확장/실험

- MarketWatch
- Barron's
- WSJ
- The Economist
- FRED/official APIs
- Paid Bloomberg/Reuters/FactSet if login/cookie automation stabilizes

## Data Type Taxonomy

| 데이터 타입 | 대표 소스 | 노션 배치 |
|---|---|---|
| 지수/히트맵/가격 차트 | Finviz, Yahoo Finance, CoinGecko | `1. 시장은 지금` |
| 경제 일정/금리확률 | Trading Economics, CME FedWatch | `1. 시장은 지금` |
| 심리/위험선호 | CNN Fear & Greed, IsabelNet, Kobeissi, Charlie Bilello | `1. 시장은 지금` 또는 `2. 이모저모` |
| 속보/헤드라인 | Reuters, Bloomberg, CNBC, Yahoo Finance, TradingView | `주요 뉴스 요약`, `2. 이모저모` |
| 차트형 리서치 | IsabelNet, Bespoke, FactSet, Advisor Perspectives | `2. 이모저모` |
| 실적 일정 | Earnings Whispers | `3. 실적/특징주` |
| 실적 정량 맥락 | FactSet, CNBC, Yahoo Finance, Finviz | `3. 실적/특징주` |
| 티커별 차트/뉴스 | Finviz, Yahoo Finance | `3. 실적/특징주` |
| 단신/환기 소재 | Reuters X, Bloomberg X, CNBC X, StockMarket.News | `2. 이모저모` 하단 또는 오프닝/클로징 후보 |

## One-Week Research Protocol

다음 단계는 감으로 분류하는 것이 아니라 5거래일 샘플 장부를 만드는 것이다.

매일 각 소스별로 다음을 기록한다.

- 수집 성공 여부
- 후보 수
- 이미지 수
- 속보성 점수: 당일 새 이슈인가?
- 방송 소재성 점수: 슬라이드 1장으로 만들 수 있는가?
- 원출처 신뢰도
- 중복률
- 실제 PPT hit 여부

권장 출력:

`projects/autopark/data/source-research/YYYY-MM-DD/source-scorecard.json`

집계 문서:

`projects/autopark/docs/source-scorecard-weekly.md`

## Source Scoring Draft

각 후보에는 다음 점수를 부여한다.

- `freshness`: 오늘/전일 새 이슈인지
- `market_relevance`: 지수, 금리, 유가, 빅테크, 실적에 직접 영향을 주는지
- `visualability`: 차트/이미지/표로 보여줄 수 있는지
- `narrative_fit`: 스토리라인 3개 중 하나에 붙는지
- `source_quality`: 원출처 신뢰도
- `novelty`: 흔한 시장 요약이 아니라 새로운 관점인지
- `broadcast_utility`: 진행자가 PPT에 바로 옮길 수 있는지

## Practical Routing Rules

- "오늘 무슨 일이 있었나"는 Reuters/Bloomberg/CNBC/Yahoo/TradingView에서 먼저 잡는다.
- "그게 시장에 왜 중요한가"는 Kobeissi/Wall St Engine/Charlie Bilello/FactSet/Advisor Perspectives로 보강한다.
- "보여줄 그림이 있나"는 IsabelNet/Bespoke/Finviz/Earnings Whispers에서 찾는다.
- "티커를 볼까"는 Finviz hot news와 일봉으로 검증한다.
- "Fed/금리 소재인가"는 Nick Timiraos, CME FedWatch, Trading Economics를 같이 본다.
- "실적 시즌인가"는 Earnings Whispers로 티커 seed를 만들고 FactSet/Finviz/CNBC/Yahoo로 맥락을 붙인다.

## Web References

- Reuters: https://reutersagency.com/en/about/about-us/
- Reuters financial markets/LSEG: https://www.lseg.com/en/data-analytics/financial-data/financial-news-coverage/global-market-news-coverage
- Bloomberg Media: https://www.bloombergmedia.com/about/
- CNBC: https://www.cnbc.com/
- Yahoo Finance app description: https://apps.apple.com/us/app/yahoo-finance-stocks-news/id328412701
- Trading Economics Calendar API: https://docs.tradingeconomics.com/economic_calendar/
- Trading Economics API overview: https://docs.tradingeconomics.com/
- Finviz: https://finviz.com/
- IsabelNet blog: https://www.isabelnet.com/blog/
- IsabelNet macro forecasts example: https://www.isabelnet.com/macro-forecasts/
- FactSet Insight: https://insight.factset.com/
- FactSet earnings topic: https://insight.factset.com/topic/earnings
- CME FedWatch user guide: https://www.cmegroup.com/tools-information/quikstrike/cme-fedwatch-tool-user-guide.html
- Advisor Perspectives global markets: https://www.advisorperspectives.com/topic/global-markets
- Bespoke Investment Group: https://www.bespokepremium.com/
