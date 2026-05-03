---
title: "Autopark Editorial Policy v1 — 04 Market Map, Heatmap, Sector Rotation, Fixed Checklist"
version: "0.1-draft"
scope: "priority_4_heatmap_sector_leaders_valuation_fixed_market_checklist"
created_for: "슈카친구들 / 위폴 아침방송 자동화 대시보드"
source_basis:
  - "박종훈의 미국주식투자 레시피: 9장 한눈에 시장을 읽는 무기, 히트맵, pp.165-203"
  - "박종훈의 미국주식투자 레시피: 부록 시장을 읽는 셀프 체크리스트, pp.237-239"
  - "보조 연결: 2번 기준서의 시그널/노이즈 및 첫 꼭지 선정 기준"
  - "보조 연결: 3번 기준서의 source_role 중 Finviz/TradingView/StockAnalysis/data_anchor/visual_anchor"
repo_context:
  - "buykings/projects/autopark: market data, visual cards, Finviz/FedWatch captures, market-radar, editorial-brief, Notion dashboard, retrospective"
status: "draft_for_market_snapshot_visual_cards_quality_gate_retrospective_design"
copyright_note: "원문 재현이 아니라 Autopark 운영 기준으로 재구성한 요약/설계 문서"
---

# Autopark Editorial Policy v1 — 04. 시장 지도·히트맵·섹터·주도주·고정 체크리스트 기준서

## 0. 한 문장 정의

Autopark의 4차 임무는 **오늘 시장의 한 장면을 찾고, 그 장면이 실제 시장 구조를 설명하는지 검증한 뒤, 방송에 쓸 시각 자료와 고정 체크리스트로 정리하는 것**이다.

```text
좋은 시장 지도 = 지수 → 히트맵 → 섹터 → 주도주 → 밸류에이션 → 고정 체크리스트가 한 흐름으로 연결된 상태
```

Autopark는 히트맵을 단순 이미지로 붙이는 도구가 아니다. 히트맵은 **오늘 돈이 어디로 갔는지**, **지수 움직임의 진짜 주인공이 누구인지**, **방송에서 한 장면으로 보여줄 만한 시장 구조가 있는지**를 판별하기 위한 시각적 증거다.

---

## 1. 이 문서의 범위

| 구분 | 포함 여부 | 설명 |
|---|---:|---|
| 미국 대표지수 해석 | 포함 | Dow, S&P500, Nasdaq, Russell2000의 역할 구분 |
| 히트맵 해석 | 포함 | 사각형 크기, 색상 강도, 섹터 위치, 자금 흐름 |
| 섹터 로테이션 | 포함 | 성장/가치, 경기민감/경기방어, 11개 GICS 섹터 |
| 시장의 주인공 찾기 | 포함 | 지수 상승·하락을 실제로 만든 대형주/섹터 판별 |
| 주도주 후보 선정 | 포함 | 섹터 강도, 시총 영향력, 지속성, 확산성 |
| 밸류에이션 가드레일 | 포함 | PER, PEG, PBR, PSR, EV/EBITDA, PCF, ROE, 마진 |
| 경기 사이클별 섹터 해석 | 포함 | 회복기, 호황기, 후퇴기, 침체기의 상대적 유리 섹터 |
| 고정 체크리스트 | 포함 | 지수, 매크로, 섹터, 특정 주식/이슈, 이벤트, 인사이트 |
| Notion 시장 지도 카드 | 포함 | 오늘의 한 장면, 섹터 로테이션, 주도주 카드 |
| 품질 게이트 | 포함 | 이미지 과다, 단일 종목 과잉해석, 작은 종목 급등 오판 방지 |
| 투자 추천 | 제외 | 특정 종목 매수·매도 추천은 금지. 방송 판단 보조만 수행 |
| 실시간 최신 데이터 값 | 제외 | 이 문서는 기준서이며, 실제 수치는 매일 파이프라인에서 주입 |

---

## 2. 책에서 추출한 핵심 운영 원칙

### 2.1 개별 종목보다 지수부터 본다

9장의 출발점은 개별 종목이 아니라 지수다. 지수는 수많은 종목 움직임을 하나의 숫자로 압축한 시장의 온도계다.

Autopark에는 다음 원칙을 적용한다.

```text
첫 화면은 항상 개별 뉴스보다 대표지수 흐름을 먼저 보여준다.
대표지수는 시장의 표면이고, 히트맵은 표면 아래의 구조다.
```

지수만 보면 “시장이 올랐다/내렸다”는 표면 판단이 가능하다. 그러나 실제로는 몇 개 대형주가 지수를 끌어올렸을 수도 있고, 반대로 지수는 약하지만 다수 종목은 견고할 수도 있다. 따라서 Autopark는 지수와 히트맵을 반드시 함께 해석해야 한다.

### 2.2 히트맵은 원인이 아니라 결과다

히트맵은 오늘 자금 흐름의 결과를 보여준다. 하지만 **왜 그런 흐름이 나타났는지**는 히트맵만으로 확정할 수 없다.

```text
히트맵 = 결과 화면
뉴스/실적/매크로 데이터 = 원인 후보
편집장 판단 = 결과와 원인을 연결하는 해석
```

따라서 Autopark는 히트맵에서 보이는 색상과 크기를 곧바로 인과관계로 해석하면 안 된다. 예를 들어 기술주가 초록색이라고 해서 자동으로 “AI 기대감 때문”이라고 쓰면 안 된다. 반드시 당일 뉴스, 실적, 금리, 경제지표, 애널리스트 반응, 주요 기사와 연결되어야 한다.

### 2.3 크기와 색을 함께 본다

히트맵에서 사각형의 크기는 시가총액 영향력을, 색상은 등락 강도를 뜻한다.

```text
큰 사각형 + 강한 색 = 지수와 시장 분위기에 미치는 영향이 큼
작은 사각형 + 강한 색 = 화제성은 크지만 시장 전체 영향은 제한적일 수 있음
큰 사각형 + 약한 색 = 조용하지만 시장 안정성 또는 지수 방향에 중요
```

Autopark는 단순 등락률 순위가 아니라 **시장 영향력**을 우선해야 한다. 중소형주가 10% 상승한 것보다 초대형주가 3% 상승한 것이 방송 첫 장면으로 더 중요할 수 있다.

### 2.4 주도주는 “많이 오른 종목”이 아니라 “시장의 선택을 받은 중심 기업”이다

주도주 후보는 다음 조건을 함께 봐야 한다.

```text
섹터 안에서 가장 강한가?
시가총액이 커서 시장 전체를 움직였는가?
하루짜리 급등이 아니라 1주일 이상 흐름이 이어지는가?
같은 섹터 또는 수혜주로 매수세가 확산되는가?
상승 이유가 펀더멘털·실적·가이던스·수급과 연결되는가?
```

Autopark는 `top_movers`를 그대로 `leaders`로 승격하면 안 된다. `top_movers`는 후보이고, `leaders`는 검증을 통과한 방송 소재다.

### 2.5 밸류에이션은 “좋은 기업 찾기”가 아니라 “가격·가치·체력 균형 확인”이다

밸류에이션이 낮다고 좋은 종목은 아니다. 낮은 이유가 일시적 악재 때문인지, 펀더멘털 훼손 때문인지 구분해야 한다.

Autopark는 종목 후보를 다룰 때 다음 세 축을 분리해야 한다.

```text
price   = 현재 주가와 밸류에이션 수준
value   = 기업의 본질 가치와 성장 가능성
quality = 꾸준히 수익을 낼 수 있는 체력과 해자
```

### 2.6 고정 체크리스트는 “매일 같은 질문을 반복하는 훈련”이다

부록의 체크리스트는 특정 날짜의 정답지가 아니라, 시장을 매일 같은 틀로 관찰하게 만드는 최소 매뉴얼이다. Autopark에는 이를 **daily market journal**로 구현한다.

```text
매일 반복되는 체크리스트가 있어야 당일 이슈의 진짜 차이를 볼 수 있다.
```

---

## 3. Autopark 시장 지도 기본 흐름

Autopark의 시장 지도는 아래 순서로 구성한다.

```text
Stage 1. 대표지수: 오늘 시장의 표면 온도
Stage 2. 히트맵: 지수 움직임의 내부 구조
Stage 3. 섹터 로테이션: 자금이 이동한 방향
Stage 4. 시장의 주인공: 지수를 실제로 움직인 기업/섹터
Stage 5. 주도주 후보 검증: 강도, 크기, 지속성, 확산성
Stage 6. 밸류에이션 가드레일: 가격·가치·체력 체크
Stage 7. 고정 체크리스트: 오늘의 시장 일지 자동 생성
```

이 흐름은 `market-radar.json`, `visual-cards`, `editorial-brief`, `Notion dashboard`에 공통으로 적용한다.

---

## 4. 대표지수 해석 기준

### 4.1 지수별 역할

| 지수 | Autopark 역할 | 방송 해석 포인트 | 주의점 |
|---|---|---|---|
| Dow Jones Industrial Average | 전통 대형 우량주·상징 지수 | 전통 산업, 대형 가치주, 경기민감 우량주의 분위기 | 구성 종목이 30개라 시장 전체 대표성은 제한적 |
| S&P500 | 미국 시장의 기준 지수 | 미국 대형주 시장 전체의 기본 방향 | 시총가중이라 빅테크 영향이 클 수 있음 |
| Nasdaq Composite / Nasdaq 100 | 기술주·성장주 온도계 | AI, 반도체, 소프트웨어, 플랫폼, 바이오 등 성장 섹터 흐름 | 변동성이 크고 금리 변화에 민감 |
| Russell2000 | 중소형주·내수 경기 온도계 | 미국 실물 경기, 금융환경, 중소기업 위험선호 | 대형주와 방향이 다를 때 시장 내부 균열 신호 가능 |

### 4.2 지수 조합별 해석

| 패턴 | 해석 후보 | Autopark 처리 |
|---|---|---|
| S&P500 상승 + Nasdaq 강세 | 성장주/기술주 중심 랠리 | 히트맵에서 빅테크·반도체·소프트웨어 확인 |
| S&P500 상승 + Dow 강세 + Nasdaq 약세 | 가치주/전통 산업 중심 순환매 | 금융·산업재·에너지·방어주 섹터 확인 |
| S&P500 상승 + Russell2000 강세 | 위험선호 확산, 내수/중소형 경기 기대 | 금리·달러·금융여건 완화 여부 확인 |
| S&P500 상승 + Russell2000 약세 | 대형주 편중 랠리 가능성 | breadth warning 태그 부여 |
| Nasdaq 강세 + 10년물 금리 하락 | 할인율 부담 완화에 성장주 반응 | FedWatch·금리 뉴스와 연결 |
| Nasdaq 약세 + 금리 상승 | 성장주 밸류에이션 부담 | 금리/물가/연준 관련 스토리 후보 |
| 지수 혼조 + 방어주 강세 | 불확실성 또는 경기 우려 | 헬스케어·필수소비재·유틸리티 확인 |
| 지수 약세 + 에너지 강세 | 인플레/유가/지정학 이슈 가능성 | 유가, 중동/러시아, OPEC, 금리 기대 확인 |

### 4.3 `index_snapshot` 스키마

```json
{
  "as_of_kst": "2026-04-21T05:10:00+09:00",
  "indexes": [
    {
      "id": "sp500",
      "display_name": "S&P 500",
      "pct_change_1d": null,
      "pct_change_5d": null,
      "pct_change_1m": null,
      "level": null,
      "role": "us_large_cap_baseline",
      "editorial_read": "미국 대형주 시장의 기본 방향",
      "needs_heatmap_confirmation": true
    },
    {
      "id": "nasdaq",
      "display_name": "Nasdaq",
      "pct_change_1d": null,
      "role": "growth_tech_temperature",
      "editorial_read": "기술주와 성장주의 위험선호"
    },
    {
      "id": "dow",
      "display_name": "Dow Jones",
      "pct_change_1d": null,
      "role": "traditional_blue_chip_temperature"
    },
    {
      "id": "russell2000",
      "display_name": "Russell 2000",
      "pct_change_1d": null,
      "role": "small_cap_real_economy_temperature"
    }
  ],
  "index_divergence": {
    "label": "broad_rally | narrow_bigtech_rally | defensive_rotation | smallcap_stress | mixed",
    "reason": "왜 이 라벨인지 한 문장"
  }
}
```

---

## 5. 히트맵 해석 기준

### 5.1 히트맵 4대 질문

Autopark는 히트맵을 볼 때 아래 질문을 순서대로 던진다.

```text
1. 오늘 시장은 큰 사각형이 움직였는가, 작은 사각형이 움직였는가?
2. 색의 강도는 특정 섹터에 집중되어 있는가, 전 시장에 퍼져 있는가?
3. 지수 상승/하락을 실제로 설명하는 주인공 기업이 있는가?
4. 이 움직임은 하루짜리 이벤트인가, 최근 1주~1개월 흐름의 연장인가?
```

### 5.2 히트맵 구성 요소별 의미

| 요소 | 의미 | Autopark 판단 |
|---|---|---|
| 사각형 크기 | 시가총액 영향력 | 지수에 미치는 힘. 큰 사각형의 색 변화는 우선 확인 |
| 색상 방향 | 상승/하락 | 미국식 표기 기준: 초록색 상승, 빨간색 하락 |
| 색상 강도 | 등락폭 | 밝을수록 강한 움직임. 단, 작은 종목의 강한 색은 과잉해석 주의 |
| 섹터 위치 | 산업군 구분 | 자금이 어느 산업군으로 이동했는지 확인 |
| 시간 프레임 | 1D, 1W, 1M 등 | 주도주 지속성 판단에 필수 |
| 지수와의 관계 | 지수 움직임의 원인 후보 | 지수 상승/하락을 누가 만들었는지 확인 |

### 5.3 히트맵 해석 라벨

```yaml
heatmap_pattern_labels:
  broad_green:
    meaning: "전반적 위험선호 또는 광범위한 매수"
    caution: "특정 섹터 주도인지 전 시장 확산인지 구분 필요"
  narrow_megacap_green:
    meaning: "대형주 편중 랠리"
    caution: "지수는 강하지만 시장 폭은 약할 수 있음"
  broad_red:
    meaning: "전반적 위험회피"
    caution: "금리, 달러, 유가, 정책 이벤트 확인"
  defensive_green_growth_red:
    meaning: "방어주 이동 또는 성장주 부담"
    caution: "경기 우려인지 금리 부담인지 분리"
  energy_green_market_red:
    meaning: "유가/지정학/인플레성 로테이션 가능성"
    caution: "에너지 강세가 시장 전체에는 악재일 수 있음"
  smallcap_red_largecap_flat:
    meaning: "실물 경기 또는 금융여건 부담이 중소형주에 집중"
    caution: "Russell2000, 은행주, 신용스프레드 확인"
  software_green_hardware_red:
    meaning: "기술주 내부 순환매"
    caution: "AI 하드웨어에서 소프트웨어로 내러티브 이동 여부 확인"
```

### 5.4 히트맵 인과관계 금지 규칙

아래 표현은 단독으로 쓰지 않는다.

```text
금지: "히트맵을 보니 AI 기대감 때문에 기술주가 올랐다."
허용: "히트맵상 기술주가 강했고, Reuters/Bloomberg/CNBC에서 AI 투자 확대와 관련된 당일 뉴스가 반복되어 AI 인프라 기대가 시장 반응의 한 원인 후보로 보인다."
```

히트맵은 결과를 보여주고, 뉴스·실적·금리·경제지표가 원인 후보를 제공한다. Autopark는 두 레이어가 함께 있을 때만 `cause_confidence`를 높인다.

---

## 6. 섹터 로테이션 기준

### 6.1 11개 섹터 기본 성격

| GICS 섹터 | 성장/가치 성격 | 경기민감/방어 성격 | Autopark 해석 |
|---|---|---|---|
| Information Technology | 성장주 | 경기민감 | 미래 이익 기대, 금리, IT 투자 사이클에 민감 |
| Communication Services | 성장주 | 경기민감 | 광고, 플랫폼, 미디어 수요와 경기 연결 |
| Consumer Discretionary | 성장주 | 경기민감 | 소비 여력과 고용·소득 환경에 민감 |
| Industrials | 가치주 | 경기민감 | 설비투자, 인프라, 물류, 경기 확장 수혜 |
| Materials | 가치주 | 경기민감 | 원자재, 건설, 제조 사이클 영향 |
| Energy | 가치주 | 경기민감 | 유가, 경기, 지정학, 인플레이션 영향 |
| Financials | 가치주 | 경기민감 | 금리, 대출, 신용, 경기순환의 핵심 |
| Real Estate | 가치주 | 경기민감 | 금리, 상업활동, 부채 조달 여건에 민감 |
| Healthcare | 혼합 | 경기방어 | 필수 수요와 혁신 성장의 혼합 |
| Consumer Staples | 가치주 | 경기방어 | 불황에도 소비 유지, 방어적 자금 이동 |
| Utilities | 가치주 | 경기방어 | 규제 산업, 안정적 현금흐름, 금리 영향 |

### 6.2 성장/가치 x 경기민감/방어 매트릭스

| 구분 | 경기민감 | 경기방어 |
|---|---|---|
| 성장주 | IT, Communication Services, Consumer Discretionary | Healthcare 일부 혁신 영역 |
| 가치주 | Financials, Industrials, Energy, Materials, Real Estate | Consumer Staples, Utilities |

### 6.3 섹터 로테이션 해석 규칙

```text
기술주·성장 산업 강세 = 성장 기대, 금리 완화, AI/소프트웨어/반도체 테마 확인
금융·산업재·에너지 강세 = 경기민감주 중심 흐름 또는 인플레/유가/금리 환경 확인
헬스케어·필수소비재·유틸리티 강세 = 방어적 자금 이동 또는 불확실성 확대 확인
부동산 강세 = 금리 하락, 금융여건 완화, 경기 회복 초입 가능성 확인
Russell2000 강세 = 위험선호 확산 또는 내수 경기 개선 기대 확인
```

### 6.4 `sector_rotation` 스키마

```json
{
  "sector_rotation": {
    "strongest_sectors": [
      {
        "sector": "Information Technology",
        "pct_change_1d": null,
        "pct_change_5d": null,
        "pct_change_1m": null,
        "style_bucket": "growth_cyclical",
        "likely_driver_candidates": ["AI capex", "rate relief", "earnings beat"],
        "confirmation_needed": ["news_cluster", "rates", "earnings_calendar"]
      }
    ],
    "weakest_sectors": [],
    "rotation_label": "growth_risk_on | value_cyclical | defensive_shift | energy_inflation | mixed",
    "broadcast_sentence": "오늘 자금은 기술 성장주 쪽으로 더 강하게 몰렸고, 방어 섹터는 상대적으로 약했습니다."
  }
}
```

---

## 7. 시장의 주인공 찾기

### 7.1 주인공 후보의 정의

`market_protagonist`는 단순히 당일 등락률이 큰 종목이 아니다. 지수와 히트맵을 함께 봤을 때 **오늘 시장 움직임을 설명하는 데 반드시 언급해야 하는 기업 또는 섹터**다.

```text
market_protagonist = 지수 움직임을 설명하는 핵심 기업/섹터/테마
leader_candidate   = 그 흐름이 지속될 경우 주도주가 될 수 있는 후보
```

### 7.2 시장 주인공 판별 질문

| 질문 | 설명 |
|---|---|
| 지수 영향력 | 이 종목이 S&P500 또는 Nasdaq 방향을 실제로 움직였는가? |
| 시총 영향력 | 초대형주라서 작은 등락도 시장 전체에 큰 영향을 주는가? |
| 섹터 대표성 | 같은 섹터의 다른 종목도 함께 움직였는가? |
| 뉴스 연결성 | 당일 뉴스, 실적, 가이던스, 애널리스트 리포트와 연결되는가? |
| 시간 지속성 | 1D 움직임인지, 1W/1M 흐름의 연장인지 확인했는가? |
| 방송 설명력 | 이 기업을 설명하면 오늘 시장 전체가 더 잘 이해되는가? |

### 7.3 시장 주인공 라벨

```yaml
market_protagonist_labels:
  megacap_driver:
    meaning: "초대형주가 지수 방향을 견인"
    example_use: "Nasdaq/S&P500 상승의 핵심 설명"
  sector_anchor:
    meaning: "특정 섹터 전체 흐름을 대표"
    example_use: "반도체, 은행, 에너지, 방어주 흐름"
  earnings_driver:
    meaning: "실적/가이던스가 섹터 또는 지수에 파급"
    example_use: "실적 시즌 첫 꼭지 후보"
  macro_proxy:
    meaning: "금리·유가·달러·경기 흐름의 대리 지표처럼 움직임"
    example_use: "은행주, 주택건설, 유틸리티, 에너지"
  sentiment_proxy:
    meaning: "개인투자자 심리 또는 테마 과열을 대표"
    example_use: "방송 보조 소재. 팩트 앵커 필요"
```

---

## 8. 주도주 후보 선정 기준

### 8.1 주도주 4대 조건

| 조건 | 판단 방식 | Autopark 필드 |
|---|---|---|
| 섹터 내 강도 | 섹터가 오를 때 더 강하게 오르고, 섹터가 내릴 때 덜 빠지는가 | `relative_sector_strength` |
| 시총 영향력 | 시총이 커서 지수와 섹터에 영향을 주는가 | `market_cap_impact` |
| 지속성 | 1D 급등이 아니라 1W/1M 흐름이 이어지는가 | `persistence_label` |
| 확산성 | 같은 섹터 후발주·수혜주로 매수세가 퍼지는가 | `spillover_score` |

### 8.2 지속성 라벨

```yaml
persistence_labels:
  one_day_spike:
    description: "하루짜리 급등. 주도주 판단 보류"
    default_action: "watch_only"
  three_day_momentum:
    description: "짧은 모멘텀. 뉴스 원인 확인 필요"
    default_action: "candidate"
  one_week_trend:
    description: "단기 추세 형성 후보"
    default_action: "leader_candidate"
  one_month_trend:
    description: "주도주 가능성 높음. 섹터 확산성 확인"
    default_action: "leader_or_theme_story"
  fading_after_spike:
    description: "초기 급등 후 힘이 약해짐"
    default_action: "drop_or_mention_only"
```

### 8.3 주도주 점수 모델

```yaml
leader_candidate_score_100:
  sector_relative_strength: 20
  market_cap_impact: 20
  persistence: 20
  spillover_to_peers: 15
  evidence_quality: 15
  valuation_quality_guardrail: 10
```

| 점수 | 라벨 | 처리 |
|---:|---|---|
| 85–100 | `leader_story` | 방송 스토리라인 또는 첫 꼭지 후보 |
| 70–84 | `strong_candidate` | Notion 상단 후보, 추가 근거 필요 |
| 55–69 | `watchlist_candidate` | 보조 카드 또는 관찰 리스트 |
| 40–54 | `mention_only` | 한 줄 언급 수준 |
| 0–39 | `drop` | 방송 소재 제외 |

### 8.4 주도주 후보 객체

```json
{
  "leader_candidate": {
    "ticker": "NVDA",
    "company_name": "NVIDIA",
    "sector": "Information Technology",
    "industry": "Semiconductors",
    "market_cap_bucket": "mega_cap",
    "price_action": {
      "pct_1d": null,
      "pct_5d": null,
      "pct_1m": null,
      "relative_to_sector_1d": null,
      "relative_to_index_1d": null
    },
    "persistence_label": "one_week_trend",
    "spillover": {
      "peer_count_positive": null,
      "related_tickers": [],
      "theme": "AI infrastructure",
      "spillover_score_0_15": null
    },
    "evidence": {
      "news_item_ids": [],
      "earnings_item_ids": [],
      "analyst_item_ids": [],
      "heatmap_visual_id": null
    },
    "valuation_guardrail": {
      "forward_pe": null,
      "peg": null,
      "roe": null,
      "gross_margin": null,
      "net_margin": null,
      "valuation_comment": "고성장 기대와 가격 부담을 함께 언급"
    },
    "leader_candidate_score": null,
    "broadcast_use": "lead_story | visual_anchor | mention_only | watchlist | drop",
    "risk_note": "하루짜리 급등인지, 이미 선반영된 기대인지 확인 필요"
  }
}
```

---

## 9. 밸류에이션 가드레일

### 9.1 밸류에이션은 스토리 승격의 보조 필터다

Autopark는 밸류에이션 데이터를 “매수/매도 추천”에 쓰지 않는다. 방송에서는 다음 역할로만 쓴다.

```text
1. 오늘 오른 종목이 이미 너무 높은 기대를 반영하고 있는지 확인
2. 저평가처럼 보이는 종목이 왜 싼지 확인
3. 주도주 후보의 상승이 실적·성장률·수익성으로 설명되는지 점검
4. 같은 테마 내에서 누가 더 시장의 신뢰를 받고 있는지 비교
```

### 9.2 핵심 지표별 사용법

| 지표 | 역할 | Autopark 주의점 |
|---|---|---|
| Forward PER | 미래 이익 대비 가격 | 예상 이익이 변하면 수치가 빠르게 무의미해질 수 있음 |
| PEG | 성장률을 반영한 PER 보완 | 고성장 테크주 평가에 유용. 1 미만, 1 내외, 1.5 이상 등 구간 참고 |
| PBR | 장부가 대비 가격 | 낮은 PBR은 저평가일 수도, 자산 효율 저하일 수도 있음 |
| PSR | 매출 대비 가격 | 이익이 없는 성장주에 사용. 매출 성장 둔화 시 위험 큼 |
| EV/EBITDA | 부채 포함 기업가치 대비 영업현금창출력 | 제조, 반도체, 감가상각 큰 산업에 유용 |
| PCF | 현금흐름 대비 가격 | PER 신뢰도 보완. 현금흐름이 중요 |
| ROE | 자기자본 효율성 | 자사주 매입·부채로 왜곡될 수 있음 |
| Gross Margin | 제품 경쟁력·비즈니스 모델 | 높다고 끝이 아니라 유지 가능성 확인 |
| Net Margin | 운영 효율·최종 수익성 | Gross와 Net 차이가 크면 비용 구조 확인 |
| Buffett Indicator | 시장 전체 과열도 | 시장 전반의 기대수익률 판단용. 개별주 판단 금지 |
| CAPE | 장기 밸류에이션 | 장기 수익률 기대치 조정용 |
| DCF/RIM | 기업 고유 가치 | 할인율 변화에 민감. 고금리 시기 보수적으로 사용 |

### 9.3 가격·가치·체력 3축 평가

```json
{
  "valuation_quality_triage": {
    "price": {
      "question": "현재 주가와 밸류에이션은 어느 수준인가?",
      "fields": ["forward_pe", "peg", "psr", "pbr"]
    },
    "value": {
      "question": "기업의 본질 가치와 성장 가능성은 무엇인가?",
      "fields": ["eps_growth", "revenue_growth", "guidance", "dcf_hint"]
    },
    "quality": {
      "question": "꾸준히 수익을 낼 체력과 해자가 있는가?",
      "fields": ["roe", "gross_margin", "net_margin", "cash_flow", "debt_ratio", "moat_notes"]
    }
  }
}
```

### 9.4 밸류에이션으로 버릴 자료

| 드롭 코드 | 조건 | 설명 |
|---|---|---|
| `cheap_for_reason` | 낮은 밸류에이션이나 실적 전망 악화 | 싸지만 펀더멘털 훼손 가능 |
| `growth_without_profit_path` | 높은 PSR + 이익 경로 불명확 | 스토리만 있고 수익화 근거 약함 |
| `roe_distortion_risk` | 높은 ROE이나 부채/자사주 매입 왜곡 가능 | 숫자 착시 가능 |
| `margin_peak_risk` | 높은 마진이나 지속성 의문 | 이미 정점일 수 있음 |
| `valuation_too_complex_for_lead` | 설명에 시간이 과도하게 필요 | 첫 꼭지보다 보조 자료 |

---

## 10. 경기 사이클과 섹터 로테이션

### 10.1 네 단계 기본 틀

경기 사이클은 정확한 예언 도구가 아니라 **현재 환경에 어떤 섹터가 상대적으로 유리한지 생각하게 만드는 틀**이다.

| 단계 | 환경 | 상대적 유리 섹터 후보 | Autopark 확인 지표 |
|---|---|---|---|
| 초기 국면 / 회복기 | 바닥 통과, 낮은 금리, 부양책, 소비·생산 재개 | 부동산, 임의소비재, 산업재 | 금리 하락, 주택 관련 지표, 소비 회복, Russell2000 |
| 중간 국면 / 호황기 | 성장 강함, 투자·고용 확대, 유동성 풍부 | 기술, 커뮤니케이션 서비스 | Capex, AI/클라우드 투자, 실적 가이던스, Nasdaq |
| 후기 국면 / 후퇴기 | 성장 둔화, 인플레 압력, 긴축 가능성 | 에너지, 헬스케어, 유틸리티 | 유가, CPI/PCE, Fed 발언, 방어 섹터 상대강도 |
| 침체 국면 | 소비·투자 위축, 시장 불안 | 필수소비재, 헬스케어, 유틸리티 | 실업률, PMI, 신용 스트레스, 방어주 강세 |

### 10.2 사이클 오판 방지 규칙

```text
사이클은 순서대로만 움직이지 않는다.
한 단계가 몇 년씩 지속될 수도 있고, 특정 단계를 건너뛰거나 되돌아갈 수도 있다.
정확한 국면 맞히기보다 현재 경제 환경과 시장 반응이 어느 쪽에 가까운지 판단한다.
```

Autopark는 `cycle_guess`를 확정 진단으로 쓰지 않고, `sector_tailwind_hint`로 쓴다.

```json
{
  "cycle_context": {
    "cycle_guess": "mid_cycle_expansion | late_cycle_moderation | contraction | recovery | unclear",
    "confidence": "low | medium | high",
    "supporting_signals": ["rates", "inflation", "employment", "fiscal_liquidity", "sector_rotation"],
    "sector_tailwind_hint": ["technology", "communication_services"],
    "do_not_overstate": true
  }
}
```

---

## 11. 고정 시장 체크리스트

### 11.1 체크리스트의 목적

고정 체크리스트는 시장을 매일 같은 프레임으로 기록하게 해준다. Autopark는 이를 `daily_market_journal`로 저장하고, Notion 첫 화면에는 압축본만 보여준다.

```text
목적 = 오늘 시장의 특징을 일기처럼 남기고, 나중에 hit/miss/false positive 회고가 가능하게 만드는 것
```

### 11.2 최소 체크리스트

| 카테고리 | 필수 항목 | Autopark 필드 |
|---|---|---|
| 미국 대표지수 흐름 | Dow, S&P500, Nasdaq, Russell2000, 오늘 시장 평가 | `index_snapshot` |
| 매크로 및 경제지표 | Fed 기준금리, 유가, 달러 인덱스, 원자재, BTC/ETH, 물가·고용 | `macro_snapshot` |
| 섹터 흐름 | 강세 섹터, 약세 섹터, 자금흐름/순환매 해석 | `sector_rotation` |
| 시장을 움직인 특정 주식과 이슈 | 핵심 종목, 관련 뉴스, 시장 반응 | `market_protagonists` |
| 중요 이벤트 | 실적 발표, FOMC, 13F, 글로벌 컨퍼런스 | `event_calendar` |
| 투자 인사이트 | 노이즈/펀더멘털 구분, 나의 대응, 향후 전략과 이유 | `daily_thesis`, `what_to_watch_next` |

### 11.3 `daily_market_journal` 스키마

```json
{
  "daily_market_journal": {
    "date_kst": "2026-04-21",
    "market_evaluation": "risk_on | risk_off | mixed | defensive | narrow_mega_cap | rotation",
    "indexes": {
      "dow": null,
      "sp500": null,
      "nasdaq": null,
      "russell2000": null,
      "one_line_read": "지수는 상승했지만 빅테크 편중이 강했습니다."
    },
    "macro": {
      "fed_policy_rate": null,
      "us10y": null,
      "oil_wti": null,
      "oil_brent": null,
      "dxy": null,
      "commodities": [],
      "btc": null,
      "eth": null,
      "inflation_employment_notes": []
    },
    "sectors": {
      "strong": [],
      "weak": [],
      "rotation_read": "기술에서 방어주로 이동하는 조짐"
    },
    "protagonists": [
      {
        "ticker": null,
        "issue": null,
        "market_reaction": null,
        "evidence_ids": []
      }
    ],
    "events": {
      "earnings": [],
      "fomc": null,
      "thirteen_f": null,
      "conferences": []
    },
    "insight": {
      "signal_or_noise": "signal | mixed | noise | unclear",
      "today_thesis": null,
      "host_action_hint": "lead_story | monitor | mention_only | drop",
      "next_watch": []
    }
  }
}
```

---

## 12. Notion 대시보드 카드 구성

### 12.1 첫 화면 추천 순서

```text
1. 오늘 시장의 한 줄 평가
2. 대표지수 4종 요약
3. 오늘의 한 장면: 히트맵 또는 대체 시각 자료
4. 강세/약세 섹터와 로테이션 해석
5. 시장의 주인공 1~3개
6. 주도주 후보와 드롭 사유
7. 고정 체크리스트 완료 상태
8. 내일/이번 주 계속 볼 지표
```

### 12.2 `오늘 시장의 한 장면` 카드

```markdown
## 오늘 시장의 한 장면

**시장 평가:** {market_evaluation_label}

**한 줄 요약:** {one_line_market_read}

**시각 자료:** {heatmap_or_chart}

**이 그림이 말해주는 것**
- 큰 사각형: {mega_cap_driver}
- 강한 섹터: {strong_sectors}
- 약한 섹터: {weak_sectors}
- 지수와 다른 점: {index_heatmap_divergence}

**과잉해석 금지**
- 히트맵은 결과이며, 원인 확정에는 {required_evidence}가 필요합니다.
```

### 12.3 `섹터 로테이션` 카드

```markdown
## 섹터 로테이션

| 구분 | 섹터 | 당일 움직임 | 1주/1개월 흐름 | 해석 |
|---|---|---:|---:|---|
| 강세 | {sector} | {pct_1d} | {pct_1w}/{pct_1m} | {read} |
| 약세 | {sector} | {pct_1d} | {pct_1w}/{pct_1m} | {read} |

**오늘의 순환매 가설:** {rotation_hypothesis}

**확인해야 할 근거:** {macro_or_news_confirmation}
```

### 12.4 `시장 주인공` 카드

```markdown
## 시장의 주인공 후보

### {ticker} — {company_name}

- **역할:** {market_protagonist_label}
- **지수 영향:** {index_impact}
- **섹터 영향:** {sector_spillover}
- **뉴스/실적 근거:** {evidence_summary}
- **지속성:** {persistence_label}
- **방송 활용:** {broadcast_use}
- **주의점:** {risk_note}
```

### 12.5 `고정 체크리스트` 카드

```markdown
## 고정 체크리스트 완료 상태

| 항목 | 상태 | 핵심 메모 |
|---|---:|---|
| 대표지수 | ✅ / ⚠️ / ❌ | {index_note} |
| 매크로 | ✅ / ⚠️ / ❌ | {macro_note} |
| 섹터 흐름 | ✅ / ⚠️ / ❌ | {sector_note} |
| 특정 주식/이슈 | ✅ / ⚠️ / ❌ | {stock_issue_note} |
| 중요 이벤트 | ✅ / ⚠️ / ❌ | {event_note} |
| 투자 인사이트 | ✅ / ⚠️ / ❌ | {insight_note} |
```

---

## 13. `market-radar` 후보 보강

### 13.1 기존 후보에 추가할 필드

```json
{
  "item_id": "visual_finviz_heatmap_20260421",
  "item_type": "heatmap | index_snapshot | sector_rotation | leader_candidate | valuation_snapshot | checklist",
  "source_role": ["data_anchor", "visual_anchor", "market_reaction"],
  "market_map": {
    "universe": "S&P500 | Nasdaq100 | Russell2000 | custom_watchlist",
    "timeframe": "1d | 1w | 1m | ytd",
    "index_context": {
      "sp500": null,
      "nasdaq": null,
      "dow": null,
      "russell2000": null
    },
    "heatmap_pattern": "narrow_megacap_green",
    "sector_rotation_label": "growth_risk_on",
    "market_protagonists": [],
    "leader_candidates": [],
    "visual_value_score": null,
    "cause_confidence": "low | medium | high"
  },
  "broadcast_fit": {
    "can_open_show": false,
    "best_slot": "opening | market_overview | sector_segment | stock_segment | appendix",
    "talk_track_hint": "오늘 시장은 지수보다 내부 구성이 더 중요합니다."
  }
}
```

### 13.2 `visual_value_score`

```yaml
visual_value_score_100:
  explains_index_move: 25
  shows_sector_rotation: 20
  highlights_market_protagonist: 20
  easy_to_understand_on_mobile: 15
  paired_with_fact_evidence: 10
  not_redundant_with_existing_chart: 10
```

| 점수 | 처리 |
|---:|---|
| 80–100 | Notion 상단 시각 자료 후보 |
| 60–79 | 관련 스토리라인 내부 자료 |
| 40–59 | 참고용. 방송 장표화는 보류 |
| 0–39 | 드롭. 이미지 과잉 방지 |

---

## 14. `editorial_brief` 출력 보강

### 14.1 추가 필드

```json
{
  "market_map_summary": {
    "one_line_market_picture": null,
    "index_divergence": null,
    "heatmap_read": null,
    "sector_rotation_read": null,
    "market_protagonists": [],
    "leader_candidates": [],
    "visual_anchor_id": null,
    "overinterpretation_warning": null
  },
  "fixed_checklist_summary": {
    "indexes_checked": true,
    "macro_checked": true,
    "sectors_checked": true,
    "specific_stocks_checked": true,
    "events_checked": true,
    "insight_written": true,
    "missing_items": []
  }
}
```

### 14.2 스토리라인 객체 보강

```json
{
  "storyline_id": "story_001",
  "title": "빅테크 몇 종목이 끌어올린 시장, 진짜 랠리인가?",
  "market_map_support": {
    "index_evidence": ["sp500", "nasdaq", "russell2000"],
    "heatmap_visual_id": "visual_finviz_sp500_1d",
    "sector_rotation_label": "narrow_growth_leadership",
    "market_protagonist_ids": ["ticker_NVDA", "ticker_MSFT"],
    "breadth_warning": true
  },
  "visual_vs_talk_role": {
    "show_as_slide": ["heatmap", "index_divergence_chart"],
    "talk_only": ["valuation nuance", "cycle context"]
  }
}
```

---

## 15. 품질 게이트

### 15.1 Market Map 품질 게이트

```text
MM-001: 대표지수 4종 중 최소 S&P500, Nasdaq, Dow는 반드시 포함한다.
MM-002: Russell2000이 없으면 중소형/실물 경기 해석을 강하게 쓰지 않는다.
MM-003: 히트맵을 붙일 때 universe와 timeframe을 명시한다.
MM-004: 히트맵 해석에는 사각형 크기와 색상 강도를 함께 언급한다.
MM-005: 히트맵만으로 원인을 확정하지 않는다.
MM-006: 섹터 강세/약세를 최소 2개 이상 기록한다.
MM-007: 시장 주인공 후보는 지수 영향력 또는 섹터 대표성을 가져야 한다.
MM-008: 등락률만으로 주도주라고 부르지 않는다.
MM-009: 주도주 후보에는 지속성 라벨이 있어야 한다.
MM-010: 주도주 후보에는 같은 섹터 확산 여부가 있어야 한다.
MM-011: 작은 종목의 급등은 시총 영향력을 확인하기 전까지 첫 꼭지로 올리지 않는다.
MM-012: 방어주 강세는 경기 우려, 금리, 불확실성 중 무엇과 연결되는지 확인한다.
MM-013: 에너지 강세는 유가·지정학·인플레이션과 연결 여부를 확인한다.
MM-014: 기술주 강세는 금리 하락, AI/반도체/소프트웨어 뉴스, 실적과 연결 여부를 확인한다.
MM-015: 밸류에이션 수치는 투자 추천이 아니라 가격 부담/품질 가드레일로만 사용한다.
MM-016: PER/PEG/ROE 등 단일 지표만으로 종목 평가를 결론 내리지 않는다.
MM-017: 고정 체크리스트 6개 카테고리 중 누락 항목을 표시한다.
MM-018: Notion 첫 화면에는 시각 자료를 과도하게 붙이지 않는다. 가장 설명력 높은 자료를 우선한다.
MM-019: 시장의 한 줄 요약은 지수·히트맵·섹터 흐름과 충돌하지 않아야 한다.
MM-020: 방송용 문장에는 불확실성을 표시한다. 예: "가능성", "원인 후보", "확인 필요".
```

### 15.2 시각 자료 드롭 규칙

| 드롭 코드 | 조건 |
|---|---|
| `visual_redundant` | 이미 같은 정보를 보여주는 더 좋은 차트가 있음 |
| `visual_too_noisy` | 한눈에 핵심이 보이지 않음 |
| `visual_no_causal_support` | 그림은 강하지만 뉴스/데이터 근거가 없음 |
| `visual_low_broadcast_value` | 방송에서 설명 시간을 줄이지 못함 |
| `visual_smallcap_overweight` | 작은 종목 급등만 강조해 시장 전체를 오해하게 함 |
| `visual_outdated_timeframe` | 당일 시장과 맞지 않는 기간의 그림 |

---

## 16. `build_editorial_brief.py` 프롬프트 블록

아래 블록은 편집장 프롬프트에 삽입할 수 있다.

```text
[MARKET MAP POLICY]

You are preparing a 07:20 KST morning market broadcast dashboard for Park Jonghoon.
Your job is not to attach every chart, but to identify the one market picture that best explains today's U.S. market.

Analyze the market in this order:
1. Start from major U.S. indexes: S&P500, Nasdaq, Dow, Russell2000 if available.
2. Compare the index move with the heatmap.
3. Identify whether the market move was broad-based, mega-cap driven, sector-driven, defensive, or mixed.
4. Identify market protagonists: companies or sectors that actually explain the index/sector move.
5. Do not call a stock a leader only because it rose sharply today. A leader candidate must show sector-relative strength, market-cap impact, persistence, and spillover to peers.
6. Use valuation only as a guardrail. Never make a buy/sell recommendation.
7. A heatmap shows results, not causes. Do not infer causality unless the move is paired with news, earnings, macro, or reliable source evidence.
8. Separate what should be shown as a chart from what should be explained verbally.
9. Finish with one concise market picture sentence.

Required fields:
- one_line_market_picture
- index_divergence
- heatmap_read
- sector_rotation_read
- market_protagonists
- leader_candidates
- visual_anchor_id
- overinterpretation_warning
- fixed_checklist_summary

Avoid:
- overclaiming from a heatmap alone
- promoting small-cap one-day spikes as market leaders
- using valuation metrics as investment advice
- attaching visuals that do not make the story easier to understand
```

---

## 17. 회고 루프에 넘길 라벨

```json
{
  "retrospective_market_map_labels": {
    "used_heatmap_as_opening_visual": "히트맵이 오프닝 장면으로 사용됨",
    "used_index_divergence": "지수 간 괴리가 방송에서 언급됨",
    "used_sector_rotation": "섹터 로테이션 해석이 방송에서 사용됨",
    "used_market_protagonist": "시장 주인공 후보가 방송에서 사용됨",
    "used_leader_candidate": "주도주 후보가 방송에서 사용됨",
    "mentioned_only_no_slide": "장표 없이 말로만 처리됨",
    "missed_market_protagonist": "대시보드가 실제 시장 주인공을 놓침",
    "missed_sector_rotation": "중요한 섹터 이동을 놓침",
    "false_positive_one_day_spike": "하루짜리 급등을 과대평가함",
    "false_positive_smallcap_noise": "중소형주 화제성을 시장 전체 신호로 오판함",
    "false_positive_heatmap_causality": "히트맵만 보고 원인을 과잉 추론함",
    "visual_too_cluttered": "시각 자료가 복잡해 방송 사용성이 낮았음",
    "visual_helped_explain_market": "시각 자료가 시장 이해를 빠르게 도왔음",
    "checklist_missing_macro": "고정 체크리스트 중 매크로 항목 누락",
    "checklist_missing_event": "고정 체크리스트 중 중요 이벤트 누락",
    "checklist_improved_next_day": "전날 체크리스트가 다음날 판단에 도움 됨"
  }
}
```

---

## 18. 구현 우선순위

### 18.1 1차 구현: `market_snapshot.json`

```text
목표: 지수, 금리, 달러, 유가, 암호화폐, 섹터 흐름을 하나의 시장 스냅샷으로 정규화
```

필수 필드:

```json
{
  "market_snapshot": {
    "date_kst": null,
    "indexes": {},
    "macro": {},
    "sector_rotation": {},
    "heatmap": {},
    "market_protagonists": [],
    "events": {},
    "checklist_status": {}
  }
}
```

### 18.2 2차 구현: `leader_candidates.json`

```text
목표: top movers와 진짜 leader candidate를 분리
```

필수 계산:

```text
relative_to_sector
relative_to_index
market_cap_bucket
persistence_1d_5d_1m
peer_spillover
news_evidence_count
valuation_guardrail
```

### 18.3 3차 구현: Notion 시장 지도 카드

```text
목표: 진행자가 07:20 전 가장 빨리 시장 구조를 이해하도록 첫 화면 구성
```

권장 카드:

```text
- 오늘 시장의 한 줄 평가
- 대표지수 요약
- 오늘의 한 장면
- 섹터 로테이션
- 시장 주인공
- 주도주 후보 / 드롭 후보
- 고정 체크리스트 완료 상태
```

### 18.4 4차 구현: 회고 비교

```text
목표: 실제 방송 자막에서 사용된 시장 그림, 섹터, 주도주를 대시보드 후보와 비교
```

비교 항목:

```text
- 실제 방송 첫 장면은 히트맵이었는가, 지수였는가, 기사였는가?
- 대시보드의 market_protagonist가 방송에 등장했는가?
- 방송에서 언급한 섹터 로테이션을 대시보드가 잡았는가?
- 주도주 후보 중 실제 사용된 것과 버려진 것은 무엇인가?
- 시각 자료가 너무 많거나 부족했는가?
```

---

## 19. `source_roles.yml`에 추가할 항목

```yaml
sources:
  finviz_heatmap:
    source_role:
      - data_anchor
      - visual_anchor
      - market_reaction
      - sector_rotation
    best_used_for:
      - "오늘 시장의 한 장면"
      - "섹터 간 자금 이동"
      - "대형주 중심 지수 영향"
      - "주도주 후보 초기 탐지"
    not_enough_for:
      - "원인 확정"
      - "펀더멘털 판단"
      - "투자 추천"
    required_pairing:
      - "major_index_snapshot"
      - "news_cluster"
      - "macro_snapshot"
      - "earnings_or_guidance_if_stock_specific"

  tradingview_heatmap:
    source_role:
      - data_anchor
      - visual_anchor
      - market_reaction
    best_used_for:
      - "시각적 대체 자료"
      - "다른 화면 구성 검증"
    required_pairing:
      - "finviz_or_index_snapshot"

  stockanalysis_heatmap:
    source_role:
      - data_anchor
      - visual_anchor
    best_used_for:
      - "Finviz 대체 확인"
      - "섹터/종목 움직임 교차검증"
```

---

## 20. Codex 구현용 의사코드

### 20.1 히트맵 패턴 분류

```python
def classify_heatmap_pattern(indexes, sectors, mega_caps, breadth=None):
    """
    indexes: dict with sp500/nasdaq/dow/russell pct changes
    sectors: list of sector performance objects
    mega_caps: list of large-cap performance objects
    breadth: optional advance/decline or percent above benchmark
    """
    spx = indexes.get("sp500", {}).get("pct_change_1d")
    nasdaq = indexes.get("nasdaq", {}).get("pct_change_1d")
    russell = indexes.get("russell2000", {}).get("pct_change_1d")

    strong_growth = sector_group_strength(sectors, ["Information Technology", "Communication Services", "Consumer Discretionary"])
    strong_defensive = sector_group_strength(sectors, ["Healthcare", "Consumer Staples", "Utilities"])
    strong_energy = sector_group_strength(sectors, ["Energy"])
    mega_cap_positive = count_positive_mega_caps(mega_caps)

    if spx and spx > 0 and mega_cap_positive >= 4 and breadth_is_weak(breadth):
        return "narrow_megacap_green"
    if strong_growth > 0 and strong_defensive < 0:
        return "growth_risk_on"
    if strong_defensive > 0 and strong_growth < 0:
        return "defensive_shift"
    if strong_energy > 0 and spx is not None and spx <= 0:
        return "energy_inflation"
    if russell is not None and spx is not None and russell < spx - 0.75:
        return "smallcap_stress"
    return "mixed"
```

### 20.2 주도주 후보 점수

```python
def score_leader_candidate(candidate):
    score = 0
    score += min(candidate.relative_sector_strength_score, 20)
    score += min(candidate.market_cap_impact_score, 20)
    score += min(candidate.persistence_score, 20)
    score += min(candidate.spillover_score, 15)
    score += min(candidate.evidence_quality_score, 15)
    score += min(candidate.valuation_quality_guardrail_score, 10)
    return score


def classify_leader_candidate(score):
    if score >= 85:
        return "leader_story"
    if score >= 70:
        return "strong_candidate"
    if score >= 55:
        return "watchlist_candidate"
    if score >= 40:
        return "mention_only"
    return "drop"
```

### 20.3 시각 자료 우선순위

```python
def score_visual_value(visual):
    score = 0
    score += 25 if visual.explains_index_move else 0
    score += 20 if visual.shows_sector_rotation else 0
    score += 20 if visual.highlights_market_protagonist else 0
    score += 15 if visual.mobile_readable else 0
    score += 10 if visual.paired_with_fact_evidence else 0
    score += 10 if not visual.redundant else 0
    return score
```

---

## 21. 제작진/저자 확인 질문

다음 질문은 박종훈 저자 또는 제작진에게 확인하면 Autopark 품질이 크게 올라갈 수 있다.

```text
1. 히트맵은 방송에서 몇 장까지 보여주는 것이 적정한가?
2. S&P500 히트맵과 Nasdaq/Russell2000 히트맵 중 어느 것을 우선 보는가?
3. 당일 1D 움직임과 1W/1M 지속성 중 방송 첫 꼭지에서는 어느 쪽을 더 중시하는가?
4. 빅테크가 지수를 끌어올린 날, 이를 첫 꼭지로 삼는 기준은 무엇인가?
5. 섹터 로테이션은 어느 정도 뚜렷해야 방송에서 말할 만한가?
6. 중소형주 급등이나 밈주식 움직임은 어떤 경우에만 언급하는가?
7. 밸류에이션 지표는 방송에서 어느 수준까지 설명하는가?
8. 주도주 후보를 장표화할 때 필요한 최소 근거는 무엇인가?
9. 고정 체크리스트에서 매일 반드시 보여줘야 하는 항목과 내부 기록만 하면 되는 항목은 무엇인가?
10. 방송 후 회고에서 “히트맵이 도움 됐다/방해됐다”를 어떻게 판단할 것인가?
```

---

## 22. 이 문서의 최종 운영 원칙

Autopark의 시장 지도는 아래 문장을 만족해야 한다.

```text
오늘 시장이 왜 그렇게 보였는지, 실제로 누가 움직였는지, 그 움직임이 하루짜리인지 흐름의 시작인지, 방송에서 무엇을 보여주고 무엇은 말로만 처리할지를 빠르게 결정하게 해준다.
```

따라서 4번 기준서의 결론은 다음 10개 질문으로 압축된다.

```text
1. 오늘 대표지수 4종은 같은 방향인가, 엇갈리는가?
2. 지수 움직임은 광범위한가, 몇 개 대형주에 편중되었는가?
3. 히트맵에서 가장 큰 색 변화는 어느 섹터와 기업에서 나타났는가?
4. 오늘 시장의 주인공은 기업인가, 섹터인가, 매크로 변수인가?
5. 강세 섹터는 성장주, 경기민감주, 경기방어주 중 어디에 가까운가?
6. 주도주 후보는 단순 급등이 아니라 지속성과 확산성을 갖는가?
7. 밸류에이션과 수익성 지표가 스토리의 과열 또는 정당성을 어떻게 보여주는가?
8. 경기 사이클상 현재 섹터 흐름은 어떤 환경과 맞물리는가?
9. 이 자료는 장표로 보여줘야 하는가, 말로만 처리해도 되는가?
10. 오늘 체크리스트에서 내일 다시 확인해야 할 항목은 무엇인가?
```

이 10개 질문을 통과한 시장 그림만 `editorial_brief`와 Notion 상단에 올라간다.
