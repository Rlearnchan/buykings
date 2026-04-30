# Autopark Source Intelligence Map

이 문서는 Autopark 소스들의 역할, 신뢰도, 자동화 우선순위를 한눈에 보기 위한 지도다.
실제 운영 절차는 `source-playbook.md`를 기준으로 한다.

## Executive Takeaways

- 속보와 일반 뉴스 후보는 BizToc, CNBC, Yahoo Finance, TradingView, Reuters 계열 feed에서 잡는다.
- Reuters 직접 웹은 차단될 수 있으므로 Reuters X, TradingView의 Reuters 기사, BizToc 후보의 Reuters 검색 링크를 같이 쓴다.
- 시장 데이터와 고정 차트는 Finviz, Yahoo Finance, Trading Economics, CNN Fear & Greed, CME FedWatch가 중심이다.
- 차트형 이모저모는 IsabelNet, Bespoke, Charlie Bilello, Liz Ann Sonders, KobeissiLetter에서 잘 나온다.
- 실적은 Earnings Whispers로 seed를 만들고 Finviz/Yahoo/CNBC/Wall St Engine/FactSet으로 숫자와 맥락을 붙인다.
- X 계정은 원문 출처라기보다 "오늘 시장이 반복하는 단어와 숫자"를 찾는 센서다.

## Source Role Table

| 소스 | 주로 얻는 데이터 | 방송 사용 | 강점 | 주의점 | 자동화 우선순위 |
|---|---|---|---|---|---|
| BizToc | 일반 웹뉴스 headline, RSS summary | 오늘의 이모저모 seed | 넓고 빠르며 요약이 붙는다 | 자체 신뢰도는 중간. Reuters 검색/원문 확인 필요 | P0 |
| Reuters | 글로벌 속보, 정책, 지정학, 기업, 시장 뉴스 | 주요 뉴스, 단신, 교차 확인 | 신뢰도와 속도 | 직접 웹 수집 401 가능. X/검색/TradingView 우회 필요 | P0 |
| CNBC | 미국 주식, 빅테크, 실적, Fed, 에너지 | 주요 뉴스, 종목 이슈 | 방송 친화적 제목과 각도 | Pro 기사 제외 필요 | P0 |
| Yahoo Finance | 가격, 차트, 종목 기사, 시장 기사 | 시장 차트, 기사 보강 | 무료 chart endpoint와 종목 coverage | 공식 API는 아님. rate limit/구조 변경 가능 | P0 |
| TradingView News | 시장 뉴스 aggregation, ticker 기사 | 뉴스 후보 pool | 다양한 기사와 ticker 후보를 빠르게 모음 | 중복/화면용 기사 많음. 점수 필터 필요 | P1 |
| Bloomberg X | 금융시장/정책/기업/기술 headline | 주요 뉴스, 단신 | money angle이 강함 | paywall 본문 접근 제한 | P0 |
| Finviz | 지수, heatmap, futures, ticker hot news | 시장은 지금, 특징주 | 화면 자체가 방송용 | Cloudflare/headless 차단 가능. persistent Chrome 필요 | P0 |
| Trading Economics | 경제 일정, 국가별 지표 | 경제 일정 | 구조화된 일정 데이터 | HTML 구조 변경 리스크. 유료 API 검토 가능 | P0 |
| CNN Fear & Greed | 투자심리 gauge | 시장 심리 체크 | 설명이 쉽다 | 캡처 의존. 내부 구성요소 자동 수집은 별도 관리 | P0 |
| CME FedWatch | FOMC 회의별 금리 확률 | Fed 패키지 | Fed funds futures 기반이라 해석이 명확 | 페이지 구조 복잡. 이벤트 주간 우선 | P1 |
| Polymarket | 이벤트 확률 | Fed/정책/지정학 보조 | 방송 질문을 만들기 좋다 | 시장 유동성과 편향 확인 필요 | P1 |
| Earnings Whispers | 실적 캘린더 이미지, ticker seed | 실적/특징주 | 주간 실적 seed로 좋다 | 이미지/OCR/시점 확인 필요 | P0 |
| FactSet Insight | 실적 시즌 정량 맥락, EPS/마진/섹터 분석 | 실적 큰 그림 | John Butters 리포트가 안정적 | 속보성은 낮고 글이 길다 | P1 |
| Wall St Engine | 빅테크 실적 숫자, quote, X 이미지 | 실적/특징주, 이모저모 | 숫자와 quote가 빠르다 | 원문 교차 확인 필수 | P0 |
| IsabelNet | 리서치 차트, valuation, sentiment | 이모저모 시각 자료 | 한 장짜리 차트가 방송에 좋다 | 차트 출처/시점/축 해석 필요 | P0 |
| Bespoke | breadth, seasonality, performance chart | 시장 내부 구조 | 읽기 쉬운 차트와 코멘트 | 유료/로그인 영역 주의 | P1 |
| Charlie Bilello | 장기 통계, 자산별 수익률, 금리/인플레 비교 | 숫자형 이모저모 | 설명 가능한 차트가 많다 | 단일 뉴스보다 통계/맥락용 | P1 |
| Kobeissi Letter | 거시 스트레스, 금리, 유가, 시장 숫자 | story seed | 시장이 반응하는 숫자를 빠르게 포착 | 과장/선별 가능성. 보조 근거 필요 | P0 |
| Liz Ann Sonders | 신뢰도 높은 시장/경제 차트 | 거시/시장 구조 | 출처 신뢰도 높음 | 가능하면 원자료까지 확인 | P1 |
| Nick Timiraos | Fed 해석과 정책 신호 | Fed 이벤트 해설 | Fed watcher로 가치 높음 | 매일 자료가 나오는 소스는 아님 | P1 |
| Advisor Perspectives | 전문 거시/자산배분 commentary | 배경 설명 | 장기 맥락에 좋음 | 속보용 아님. 403 가능 | P2 |
| StockMarket.News / _Investinq | 단신, quote, 시각 자료 seed | 단신/쉬어가기 | 소재 발굴이 빠름 | 원출처 확인 필수 | P2 |

## 현재 Autopark 수집 구조

### Batch A: 일반 웹뉴스

현재 기본 소스:

- BizToc
- Reuters
- CNBC
- TradingView News
- Yahoo Finance

운영 방식:

- BizToc은 RSS feed를 사용한다.
- BizToc 후보는 headline, summary, Reuters 검색 링크를 evidence로 가진다.
- CNBC/Yahoo/TradingView는 HTML anchor 기반 후보를 만든다.
- Reuters 직접 웹은 401이 날 수 있으므로 실패해도 배치를 중단하지 않는다.

### Batch B: 특수/리서치/X

현재 starter set:

- IsabelNet
- FactSet Insight
- Advisor Perspectives
- Kobeissi Letter
- StockMarket.News / _Investinq
- Liz Ann Sonders
- Bespoke
- Nick Timiraos

운영 방식:

- IsabelNet/FactSet은 RSS 또는 HTML 기반 수집 후보가 있다.
- X 계정은 browser profile 기반 추출이다.
- X는 headline + image + 반응 지표를 주로 보고, 사실 관계는 다른 출처로 확인한다.

### 고정 시장 데이터

주요 소스:

- Finviz
- Yahoo Finance
- Trading Economics
- CNN Fear & Greed
- CME FedWatch
- Polymarket
- CoinGecko

운영 방식:

- 고정 데이터는 "시장은 지금"의 뼈대다.
- 뉴스 후보보다 안정성과 재현성이 중요하다.
- 캡처 실패 시 해당 카드만 graceful degradation해야 한다.

## Recommended Source Tiers

### Tier 0: 매일 고정

- Finviz
- Yahoo Finance
- Trading Economics
- CNN Fear & Greed
- Earnings Whispers
- BizToc
- CNBC
- Reuters X / Reuters 검색 / TradingView Reuters
- Bloomberg X
- Wall St Engine
- KobeissiLetter
- IsabelNet

### Tier 1: 조건부 또는 주 2-3회

- CME FedWatch
- Polymarket
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
- FT
- The Economist
- StockMarket.News / _Investinq
- FRED/official APIs
- paid Bloomberg/Reuters/FactSet, if login automation stabilizes

## Data Type Taxonomy

| 데이터 타입 | 대표 소스 | 배치 섹션 |
|---|---|---|
| 지수/heatmap/가격 차트 | Finviz, Yahoo Finance, CoinGecko | 시장은 지금 |
| 경제 일정/금리 확률 | Trading Economics, CME FedWatch | 시장은 지금, Fed 패키지 |
| 심리/위험 신호 | CNN Fear & Greed, IsabelNet, Kobeissi, Charlie Bilello | 시장은 지금, 이모저모 |
| 속보/headline | Reuters, Bloomberg, CNBC, Yahoo Finance, TradingView, BizToc | 주요 뉴스, 이모저모 |
| 차트형 리서치 | IsabelNet, Bespoke, FactSet, Advisor Perspectives | 이모저모 |
| 실적 일정 | Earnings Whispers | 실적/특징주 |
| 실적 정량 맥락 | FactSet, CNBC, Yahoo Finance, Finviz, Wall St Engine | 실적/특징주 |
| ticker별 뉴스/차트 | Finviz, Yahoo Finance, TradingView | 실적/특징주 |
| 단신/쉬어가기 | Reuters X, Bloomberg X, CNBC X, StockMarket.News, BizToc | 단신, 이모저모 |

## Practical Routing Rules

- "오늘 무슨 일이 있었나?"는 BizToc/CNBC/Yahoo/TradingView/Reuters 계열에서 먼저 찾는다.
- "그게 시장에 왜 중요한가?"는 Kobeissi/Wall St Engine/FactSet/Bespoke/Charlie Bilello로 보강한다.
- "보여줄 그림이 있나?"는 Finviz/IsabelNet/Bespoke/Earnings Whispers에서 찾는다.
- "이 ticker가 진짜 움직였나?"는 Finviz와 Yahoo로 확인한다.
- "Fed/금리 소재인가?"는 Nick Timiraos, CME FedWatch, Trading Economics를 함께 본다.
- "실적 시즌인가?"는 Earnings Whispers로 seed를 만들고 FactSet/Finviz/CNBC/Yahoo로 맥락을 붙인다.

## Source Scoring Draft

각 후보에는 다음 축으로 점수를 준다.

- `freshness`: 오늘/전일 이슈인가?
- `market_relevance`: 지수, 금리, 유가, 빅테크, 실적에 직접 영향이 있는가?
- `visualability`: 차트, 이미지, 표, 숫자 카드로 보여줄 수 있는가?
- `narrative_fit`: 방송의 큰 질문 중 하나에 붙는가?
- `source_quality`: 원출처가 믿을 만한가?
- `novelty`: 흔한 시장 요약이 아니라 새로운 관점인가?
- `broadcast_utility`: 진행자가 바로 말하거나 PPT 한 장으로 만들 수 있는가?

## One-Week Research Protocol

일주일 동안 각 소스별로 다음 값을 기록하면 소스 품질을 수치화할 수 있다.

- 수집 성공 여부
- 후보 수
- 이미지/차트 후보 수
- 속보성 점수
- 방송 소재 점수
- 원출처 신뢰도
- 중복률
- 실제 PPT 채택 여부

권장 출력:

`projects/autopark/data/source-research/YYYY-MM-DD/source-scorecard.json`

집계 문서:

`projects/autopark/docs/source-scorecard-weekly.md`

## Known Gaps

- `today_misc_sources.json`의 일부 `broadcast_use` 한글이 깨져 있다.
- `enabled=false`가 많아 실제 운영 기본값과 설정상의 enabled 상태가 아직 분리되어 있다.
- paywall 소스의 자동화 정책이 더 명확해야 한다.
- X 계정별 개별 프로필은 아직 더 세밀하게 나눌 수 있다.
- BizToc은 넓은 후보에는 좋지만 시장 관련성 필터를 계속 다듬어야 한다.
