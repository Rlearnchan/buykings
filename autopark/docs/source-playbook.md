# Autopark Source Playbook

이 문서는 Autopark가 매일 아침 방송 준비 대시보드를 만들 때 각 소스를 어떤 역할로 써야 하는지 정리한다. `source-intelligence-map.md`가 넓은 분류표라면, 이 문서는 실제 운영용 플레이북이다.

## Source Tiers

### P0: 매일 본다

| 소스 | 주로 얻는 것 | Notion 배치 | 운영 규칙 |
|---|---|---|---|
| Finviz | 주요 지수, S&P500/러셀 히트맵, 티커 일봉, 티커 hot news | `시장은 지금`, `실적/특징주` | 시장 루틴과 특징주 차트의 기본 소스. 티커 뉴스 한 줄이 있으면 같이 캡처한다. |
| Yahoo Finance | 지표/선물/환율/주식 가격, 기사 후보 | Datawrapper, 보강 기사 | 무료 chart endpoint로 시장 차트를 만들고, 기사 후보는 원문 검증용으로 쓴다. |
| CoinGecko | 비트코인 가격 | Datawrapper | BTC는 주식장과 다르게 실시간성이 있으므로 수집 시점 기준으로 표기한다. |
| Trading Economics | 경제 일정, 국가/중요도/예상치 | 경제 일정 표 | 미국은 2스타 이상, 미국 외는 3스타만 노출한다. |
| CNN Fear & Greed | 위험선호 게이지 | `시장은 지금` | 한 장으로 투자심리를 보여준다. |
| Earnings Whispers | 주간 실적 캘린더, ticker seed | `실적/특징주` | 실적 시즌의 출발점. 이미지 고정 삽입 후 ticker drilldown을 건다. |
| Wall St Engine | 빅테크 실적 숫자, 기업 quote, after-hours 반응 | `실적/특징주`, `이모저모` | 빅테크 실적일에는 최우선 X 소스. 이미지와 텍스트를 많이 수집한다. |
| Reuters/Bloomberg/CNBC X | 속보, 단신, 정책/기업 headline | `주요 뉴스`, `이모저모`, `단신/환기` | 공개 X 계정은 페이월 우회가 아니라 headline 레이더로 쓴다. |
| KobeissiLetter | 금리, 유가, 포지셔닝, macro stress 숫자 | `이모저모`, story seed | 과장 가능성은 있지만 시장이 주목하는 숫자를 잘 잡는다. |
| IsabelNet | IB/리서치 차트, 거시/포지셔닝 이미지 | `이모저모` | 차트형 자료로 좋다. 다만 당일 thesis와 붙지 않으면 하단 후보로 둔다. |

### P1: 조건부로 본다

| 소스 | 주로 얻는 것 | 쓰는 날 |
|---|---|---|
| Polymarket | Fed/정책/선거/지정학 이벤트 확률 캡처 | FOMC, 대선/정책, 지정학 이벤트가 시장 중심일 때 |
| CME FedWatch | FOMC 회의별 금리확률 | Fed 주간, CPI/PCE/FOMC 직후 |
| FactSet Insight | 실적 시즌 정량 context, EPS/마진/섹터 | 실적 시즌 큰 그림이 필요할 때 |
| Bespoke | breadth, seasonality, 시장 내부 구조 | 시장 강세/과열/폭 조정 이야기가 필요할 때 |
| Charlie Bilello | 장기 시장 차트, 자산별 수익률 | 숫자형 이모저모, 유가/금리/인플레 비교 |
| Liz Ann Sonders | 신뢰도 높은 시장/거시 차트 | 경기/시장 내부 구조 |
| Nick Timiraos | Fed 해석 | Fed 이벤트 전후 |
| TradingView News | 넓은 뉴스 후보 pool | Batch A 보강용. 중복/평면 기사 많으니 선별 점수 필요 |

### P2: 실험/보조

- Advisor Perspectives: 장문 거시 배경. 매일 아침 속보보다는 주간/월간 맥락.
- StockMarket.News / _Investinq: 화제성 영상/quote. 원출처 확인 후 단신으로만 사용.
- MarketWatch/Barron's/WSJ/Economist: 공개 headline 또는 구독 profile 자동화가 안정화된 뒤 확장.

## Slot별 소스 사용법

### 1. 시장은 지금

고정 순서:

1. Finviz 주요 지수 흐름
2. S&P500 히트맵
3. 러셀2000 히트맵
4. 미국 10년물 국채금리
5. WTI
6. 브렌트
7. DXY
8. 원달러
9. 비트코인
10. CNN Fear & Greed
11. 미국 경제 일정
12. 글로벌 경제 일정

추가 조건:

- 0430처럼 진행자가 S&P500/나스닥 일봉/주봉을 본 날은 지수 차트 보강을 검토한다.
- 금리/FOMC가 핵심인 날은 시장 루틴 뒤에 `Fed package`를 별도 배치한다.

### 2. Fed / FOMC Package

FOMC, CPI, PCE, 고용보고서 직후에는 경제 일정 표만으로 부족하다.

필수 자료:

- FOMC 성명서 핵심 bullet
- 이전 성명 대비 문구 변화
- Powell 발언 요약
- FedWatch 또는 Polymarket 금리인하 베팅
- 10년물, DXY, WTI 반응

배치 방식:

- `시장은 지금` 바로 뒤 또는 `오늘의 이모저모` 최상단에 둔다.
- 제목은 `FOMC 이후 시장이 보는 금리 경로`처럼 방송 질문형으로 짧게 쓴다.

### 3. 오늘의 이모저모

좋은 이모저모는 “재밌는 자료”가 아니라 “스토리라인에 붙일 수 있는 자료”다.

선정 기준:

- 자료 하나가 슬라이드 1장을 만들 수 있는가?
- 아래/위 자료와 연결되어 흐름을 만들 수 있는가?
- 원문 headline보다 한국어 짧은 제목으로 바꿨을 때 힘이 있는가?
- 차트/이미지/quote가 실제로 볼 만한가?

소스별 역할:

- IsabelNet/Bespoke/Charlie Bilello: 차트형 맥락
- Reuters/Bloomberg/CNBC: 당일 headline
- KobeissiLetter: 시장이 반응하는 숫자
- Wall St Engine: 기업/실적 quote
- Polymarket: 확률형 이벤트 소재

### 4. 실적/특징주

실적 시즌의 기본 flow:

1. Earnings Whispers 주간 캘린더를 넣는다.
2. 캘린더 ticker 중 당일/전일 실적 발표 또는 after-hours 급등락 ticker를 추린다.
3. Wall St Engine에서 해당 ticker의 숫자/quote/image를 우선 찾는다.
4. Yahoo/Finviz에서 뉴스와 주가 반응을 확인한다.
5. Finviz 일봉 또는 5분봉/after-hours 차트를 붙인다.

빅테크 실적 카드 필드:

- EPS actual vs estimate
- revenue actual vs estimate
- 핵심 사업 성장률: cloud, AWS, ads, search, personal computing 등
- AI 관련 숫자: run-rate, CAPEX, RPO/backlog, TPU, data center
- guidance 또는 비용 우려
- after-hours 반응
- 방송용 한 줄 해석

0430 기준 예시:

- MSFT: cloud 39%, AI run-rate $37B, RPO $627B, AI 비용 증가 우려
- AMZN: AWS 28%, AI data center/self-chip CAPEX $200B
- META: 광고 33%, EPS surprise, CAPEX +$10B
- GOOGL: cloud 63%, EPS surprise, backlog $460B
- QCOM/ON/INTC: 반도체 후속 흐름과 5분봉/일봉

### 5. 단신 / 환기 소재

단신은 메인 스토리와 경쟁시키지 않는다.

좋은 단신:

- 방송 분위기를 바꿀 수 있다.
- 정치/기업인/문화/기술 소재지만 시장 이야기에 살짝 닿는다.
- 1-2장으로 끝낼 수 있다.

대표 소스:

- Reuters/Bloomberg/CNBC X
- StockMarket.News
- Wall St Engine
- Polymarket trending markets

0430 예시:

- Musk/SpaceX Mars 보상 조건
- 책/댓글 오프닝은 개인 소재라 자동화 제외

## Candidate Scoring

후보는 단순 언급량이 아니라 다음 축으로 평가한다.

| 점수 | 질문 |
|---|---|
| freshness | 오늘/전일 새 이슈인가? |
| section_fit | 시장/Fed/이모저모/실적/단신 중 위치가 명확한가? |
| visualability | 캡처/차트/표/숫자 카드로 보여줄 수 있는가? |
| narrative_tension | 대립축을 만드는가? |
| theme_proof | 큰 테마를 증명하는 사례인가? |
| source_quality | 원출처가 믿을 만한가? |
| broadcast_utility | 진행자가 바로 말할 수 있는가? |

0430 이후에는 `section_fit`과 `theme_proof`를 언급량보다 높게 둔다.

## Common Failure Modes

- 속보가 크다고 상단 story로 밀어 올리는 것. 실제 방송은 속보보다 전개가 좋은 소재를 고른다.
- X 자료를 너무 많이 넣는 것. Wall St Engine처럼 역할이 뚜렷한 계정만 우선 노출한다.
- 이모저모에 원문을 그대로 싣는 것. 제목과 quote는 한국어 방송용으로 재작성해야 한다.
- 실적 후보를 ticker 리스트로 끝내는 것. 숫자와 주가 반응이 있어야 한다.
- Fed 이벤트를 경제 일정에만 남기는 것. FOMC 날에는 별도 해석 패키지가 필요하다.
