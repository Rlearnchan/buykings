# Autopark Source Playbook

이 문서는 Autopark가 아침 방송 준비용 자료를 만들 때 각 소스를 어떤 역할로 써야 하는지 정리한다.
핵심 원칙은 "많이 긁기"가 아니라, 방송에 바로 쓸 수 있는 질문과 그림을 빠르게 찾는 것이다.

## 운영 원칙

- 일반 뉴스는 BizToc/CNBC/Yahoo/TradingView에서 후보를 넓게 잡고, Reuters 검색이나 원문 기사로 교차 확인한다.
- X 계정은 사실 확정 소스가 아니라 "시장이 지금 어떤 숫자와 문장을 반복하는지" 보는 레이어로 쓴다.
- 차트/리서치 소스는 단독 뉴스보다 방송용 그림, 맥락, 비교축을 제공할 때 가치가 크다.
- 실적/특징주 후보는 ticker만 뽑지 말고 숫자, 주가 반응, 왜 지금인지까지 붙어야 한다.
- paywall 소스는 본문 요약보다 headline, 공개 이미지, 공개 X 피드를 우선한다.

## P0: 매일 보는 소스

| 소스 | 주 역할 | 배치 | 운영 메모 |
|---|---|---|---|
| Finviz | 지수 흐름, S&P500/Russell heatmap, 특징주, ticker hot news | 시장은 지금, 실적/특징주 | 화면 자체가 방송용이다. 특징주 출발점으로 가장 좋다. |
| Yahoo Finance | 가격/수익률/종목 기사, 무료 chart endpoint | 시장 차트, 기사 보강 | Datawrapper 차트와 궁합이 좋다. 기사 후보는 원문 확인용으로 쓴다. |
| Trading Economics | 경제 일정, 국가별 중요 지표 | 경제 일정 | 미국 2성 이상, 비미국 3성 이상을 기본으로 본다. |
| CNN Fear & Greed | 투자심리 게이지 | 시장은 지금 | 한 장으로 시장 온도를 설명하기 좋다. |
| Earnings Whispers | 주간 실적 캘린더, ticker seed | 실적/특징주 | 실적 주간의 seed. 이후 Finviz/Yahoo/Wall St Engine으로 drilldown한다. |
| BizToc | 넓은 일반 뉴스 headline/summary seed | 오늘의 이모저모 | RSS 요약으로 후보를 잡고 Reuters 검색 링크로 교차 확인한다. |
| CNBC | 미국 시장/기업/실적/Fed/에너지 기사 | 주요 뉴스, 오늘의 이모저모 | 방송 톤과 맞는 제목이 많다. CNBC Pro와 일반 기사를 분리해서 본다. |
| Reuters X / TradingView Reuters | 속보, 정치/지정학/기업/시장 headline | 주요 뉴스, 단신 | Reuters 직접 웹은 401이 날 수 있으므로 X/TradingView/검색 링크를 함께 쓴다. |
| Bloomberg X | 금융시장, 정책, 기업, 기술의 money angle | 주요 뉴스, 단신 | paywall 본문보다 공개 headline과 이미지 중심으로 쓴다. |
| Wall St Engine | 빅테크 실적 숫자, 기업 quote, after-hours 반응 | 실적/특징주, 이모저모 | 빅테크 실적일에 우선순위가 높다. 원문/수치 교차 확인은 필수다. |
| Kobeissi Letter | 금리, 유가, 거시 스트레스, 시장 숫자 | 이모저모, story seed | 주목도 높은 숫자를 빨리 건진다. 과장 가능성을 감안해 보조 근거를 붙인다. |
| IsabelNet | 리서치 차트, 밸류에이션, sentiment, recession, positioning | 이모저모 | 그림 재료로 좋다. 출처/시점/축 해석을 확인하고 쓴다. |

## P1: 조건부로 보는 소스

| 소스 | 주 역할 | 보는 조건 |
|---|---|---|
| CME FedWatch | FOMC 회의별 금리 확률 | FOMC, CPI, PCE, 고용보고서 전후 |
| Polymarket | 이벤트 확률, 정책/지정학/선거 기대 | 확률이 이야기의 긴장을 만들 때 |
| FactSet Insight | S&P500 실적 시즌 정량 맥락, EPS/매출/마진/섹터 | 실적 시즌의 큰 그림이 필요할 때 |
| Bespoke | breadth, seasonality, performance, positioning chart | 시장 과열/조정/강세 구조를 설명할 때 |
| Charlie Bilello | 장기 자산별 수익률, 금리/인플레/시장 통계 | 숫자형 이모저모나 비교 차트가 필요할 때 |
| Liz Ann Sonders | 신뢰도 높은 시장/경제 차트 | 경기/시장 내부 구조를 설명할 때 |
| Nick Timiraos | Fed 해석과 정책 신호 | Fed 이벤트 전후 |
| TradingView News | 넓은 시장 뉴스 aggregation | Batch A 보강. 중복과 화면용 기사 필터링 필요 |
| Advisor Perspectives | 전문 거시/자산배분 commentary | 매일 속보보다 주간/월간 배경 설명이 필요할 때 |

## P2: 보조/실험 소스

| 소스 | 용도 |
|---|---|
| MarketWatch, Barron's, WSJ, FT, Economist | 공개 headline 확인, 향후 구독/브라우저 프로필 자동화 후보 |
| StockMarket.News / _Investinq | 단신, quote, 시각 자료 seed. 반드시 원출처 확인 |
| Community/curiosity sources | 방송 분위기 전환용 소재. 시장 섹션의 핵심 근거로 쓰지 않는다. |
| Workflow tools | 번역, LLM, 시각 보조 도구. 수집 대상이 아니라 작업 보조다. |

## 섹션별 라우팅

### 1. 시장은 지금

고정 순서:

1. Finviz 지수/heatmap
2. Yahoo Finance 가격 차트
3. 10년물, WTI/Brent, DXY, USD/KRW, Bitcoin
4. CNN Fear & Greed
5. 미국/글로벌 경제 일정
6. 필요 시 CME FedWatch 또는 Polymarket

좋은 후보는 "지금 시장이 왜 움직였는지"와 "한 장으로 보여줄 그림"을 동시에 가진다.

### 2. 주요 뉴스 / 오늘의 이모저모

기본 흐름:

1. BizToc에서 넓은 headline/summary 후보를 잡는다.
2. CNBC/Yahoo/TradingView에서 시장 관련 후보를 보강한다.
3. Reuters 검색 링크나 공개 Reuters/X/TradingView 기사로 사실관계를 확인한다.
4. IsabelNet/Bespoke/Charlie Bilello에서 그림이 되는 보조 자료를 찾는다.
5. 제목은 원문 직역보다 한국어 방송 질문형으로 바꾼다.

좋은 이모저모는 "흥미롭다"에서 끝나지 않고 시장, 기업, 소비자 행동, 정책 중 하나와 연결된다.

### 3. Fed / FOMC 패키지

필수 재료:

- FOMC 성명 핵심 문구 변화
- Powell 발언 요약
- CME FedWatch 또는 Polymarket 확률 변화
- 10년물, DXY, WTI, 주요 지수 반응
- Nick Timiraos나 Reuters/Bloomberg/CNBC의 해석 headline

배치 방식은 "시장과 금리 경로가 충돌하는 지점"을 질문으로 잡는 것이 좋다.

### 4. 실적 / 특징주

기본 흐름:

1. Earnings Whispers에서 발표 예정 ticker seed를 잡는다.
2. Finviz에서 주가 반응과 hot news를 본다.
3. Yahoo/CNBC/TradingView로 기사 맥락을 붙인다.
4. Wall St Engine에서 숫자와 quote가 있으면 보강한다.
5. FactSet으로 시즌 전체 맥락을 붙인다.

빅테크 실적 카드 필드:

- EPS actual vs estimate
- revenue actual vs estimate
- cloud, ads, search, AWS, Azure, AI, CAPEX, RPO/backlog 같은 사업부 숫자
- guidance와 비용 우려
- after-hours 또는 premarket 반응
- 방송에서 한 문장으로 말할 해석

### 5. 단신 / 쉬어가는 소재

단신은 메인 스토리를 압도하지 않아야 한다.

좋은 단신:

- 방송 분위기를 바꿔준다.
- 정치/기업/문화/기술 소재지만 시장 이야기와 한 다리 연결된다.
- 1-2문장으로 끝낼 수 있다.

주요 소스:

- Reuters/Bloomberg/CNBC X
- StockMarket.News
- Wall St Engine
- Polymarket trending markets
- BizToc curiosity 후보

## 후보 점수 기준

| 축 | 질문 |
|---|---|
| freshness | 오늘/전일 이슈인가? |
| section_fit | 시장/Fed/이모저모/실적/단신 중 위치가 명확한가? |
| visualability | 차트, 이미지, 숫자 카드로 보여줄 수 있는가? |
| narrative_tension | 진행자가 던질 질문이 생기는가? |
| theme_proof | 오늘 방송의 큰 테마를 증명하거나 반박하는가? |
| source_quality | 원출처가 믿을 만한가? |
| broadcast_utility | 바로 말하거나 PPT 한 장으로 만들 수 있는가? |

## 흔한 실패 모드

- 속보가 많다는 이유만으로 상단 스토리로 올리는 것.
- X 소재를 사실 확정처럼 쓰는 것.
- 이모저모에 원문 제목만 나열하는 것.
- 실적 후보를 ticker 리스트로만 내보내고 숫자와 주가 반응을 빼는 것.
- Fed 이벤트를 경제 일정으로만 처리하고 금리 확률/시장 반응을 붙이지 않는 것.
- paywall 기사 본문에 접근하지 못했는데 본문을 읽은 것처럼 쓰는 것.
