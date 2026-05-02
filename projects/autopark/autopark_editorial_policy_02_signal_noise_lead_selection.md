---
title: "Autopark Editorial Policy v1 — 02 Signal/Noise & Lead Selection"
version: "0.1-draft"
scope: "priority_2_lead_story_selection_signal_noise_expectation_gap_prepricing"
created_for: "슈카친구들 / 위폴 아침방송 자동화 대시보드"
source_basis:
  - "박종훈의 미국주식투자 레시피: 2장 시그널과 노이즈를 구분하는 법, pp.26-47"
  - "박종훈의 미국주식투자 레시피: 3장 뉴스 속 숨은 신호를 읽어라, pp.48-61"
  - "박종훈의 미국주식투자 레시피: 10장 실적 발표로 시장을 읽는 법, pp.204-211"
repo_context:
  - "buykings/projects/autopark: market-radar 후보 → editorial-brief 추천 스토리라인 → Notion 발행 → 방송 후 회고"
status: "draft_for_prompt_scoring_quality_gate_design"
copyright_note: "원문 재현이 아니라 Autopark 운영 기준으로 재구성한 요약/설계 문서"
---

# Autopark Editorial Policy v1 — 02. 첫 꼭지 선정 / 시그널·노이즈 기준서

## 0. 한 문장 정의

Autopark의 2차 임무는 수집된 뉴스와 자료를 보고 **오늘 7:20 방송의 첫 꼭지가 될 만한 구조적 신호와, 버리거나 보조로만 써야 할 소음을 구분하는 것**이다.

```text
좋은 첫 꼭지 = 오늘 시장을 실제로 움직인 원인 + 구조적 영향 + 기대 대비 변화 + 방송에서 설명 가능한 그림/문장
```

따라서 이 문서는 `editorial_brief.storylines[*]`의 `rank`, `recommendation_stars`, `lead_candidate_reason`, `signal_or_noise`, `evidence_to_use`, `evidence_to_drop`을 결정하는 기준서다.

---

## 1. 이 문서의 범위

| 구분 | 포함 여부 | 설명 |
|---|---:|---|
| 첫 꼭지 선정 기준 | 포함 | 추천 스토리라인 중 무엇을 1번으로 올릴지 판단 |
| 시그널/노이즈 판정 | 포함 | 구조적 변화인지 단기 소음인지 분류 |
| 기대 대비 결과 판단 | 포함 | 컨센서스, 내재 기대, 가이던스, 가격 반응의 괴리 |
| 선반영 판단 | 포함 | 이미 가격에 반영된 기대와 새로 반영될 변수를 분리 |
| 실적 발표 해석 | 포함 | 숫자, 컨센서스, 어닝콜, 가이던스, 경영진 톤 |
| 뉴스 반응 속도 | 포함 | 정책 뉴스와 기업 뉴스의 반응 방식 차이 |
| 소스별 역할 | 제외 | 4장·5장 기준서에서 별도 작성 예정 |
| 히트맵/섹터 상세 판단 | 일부 포함 | 첫 꼭지 평가용으로만 포함. 세부는 9장 기준서에서 작성 예정 |
| 회고 runbook 결합 | 일부 포함 | 라벨 후보만 제안. 최종 결합은 5단계 문서에서 작성 예정 |

---

## 2. 책에서 추출한 핵심 운영 원칙

### 2.1 뉴스의 무게는 같지 않다

모든 뉴스는 같은 비중으로 다루면 안 된다. Autopark는 수집 단계에서는 넓게 모으되, 편집장 단계에서는 아래 질문을 먼저 던져야 한다.

```text
이 뉴스는 단기 이벤트인가, 구조적 변화인가?
정책·금리·경제지표·기술 혁신 같은 거시 변수와 연결되는가?
특정 기업이 아니라 산업 전반의 수익 모델이나 자금 흐름을 바꿀 수 있는가?
```

이 질문에 답하지 못하는 뉴스는 방송 소재가 될 수는 있어도 첫 꼭지 후보로는 약하다.

### 2.2 노이즈는 대개 “이미 알려졌거나, 검증되지 않았거나, 본질을 건드리지 않는다”

노이즈 후보의 공통점은 다음과 같다.

| 노이즈 유형 | 설명 | Autopark 처리 |
|---|---|---|
| `already_known` | 오래 반복되어 이미 가격과 시장 공감대에 반영된 이슈 | 첫 꼭지 금지. 새 정보가 있을 때만 재평가 |
| `unverified_rumor` | 익명 관계자, 확인되지 않은 M&A설, 루머성 기술 유출 | fact evidence 사용 금지 |
| `celebrity_comment_only` | 유명인·정치인·CEO의 단편 발언이지만 정책/실적 변화 없음 | sentiment 또는 watch-only |
| `minor_management_noise` | 단순 보직 변경, 상징적 인터뷰, 화제성 기사 | 핵심 전략 변화가 아니면 drop |
| `no_fundamental_link` | 매출, 이익, 현금흐름, 시장점유율, 경쟁구도와 무관 | drop 또는 보조 멘트 |
| `sentiment_only` | X/Reddit에서만 뜨겁고 팩트·가격 반응·공식 자료가 약함 | 훅으로만 제한, 첫 꼭지 근거 금지 |
| `duplicate_theme` | 더 강한 스토리라인에 이미 포함되는 반복 소재 | 병합 또는 drop |

노이즈라고 해서 전부 무시하라는 뜻은 아니다. 노이즈는 시장 심리나 군중 반응을 보여주는 보조 자료가 될 수 있다. 다만 **투자 판단의 중심축이나 첫 꼭지의 근거로 쓰면 안 된다.**

### 2.3 시그널은 “돈 버는 능력” 또는 “할인율/정책 경로”를 바꾼다

시그널 후보는 다음 중 하나 이상을 건드린다.

| 시그널 축 | 판단 질문 | 대표 자료 |
|---|---|---|
| `rates_signal` | 금리 경로, 할인율, 유동성, 성장주 밸류에이션을 바꾸는가? | Fed, 금리, FedWatch, 국채금리, FOMC 발언 |
| `macro_signal` | 물가, 고용, 소비, 경기, GDP, 달러·유가 흐름을 바꾸는가? | CPI/PCE/PPI, 고용, ISM, 소매판매, GDPNow |
| `earnings_signal` | 기업의 현재 가치와 미래 가치를 동시에 재평가하게 하는가? | 실적, 마진, 매출, EPS, 가이던스, 어닝콜 |
| `policy_signal` | 규제, 관세, 보조금, 세금, 산업 정책이 비용·수요·공급망을 바꾸는가? | 행정부/의회/규제기관 발표, 무역정책 |
| `industry_structure_signal` | 특정 산업의 경쟁구도, 수익모델, 시장점유율을 재편하는가? | 기술 혁신, 대규모 수주, 신약 임상, 플랫폼 변화 |
| `market_structure_signal` | 자금 흐름, 섹터 로테이션, 위험 선호를 바꾸는가? | 지수, 섹터, 히트맵, 크레딧, VIX, 달러 |

시그널 여부를 판단하는 기본 질문은 다음 세 가지다.

```text
1. 이 정보가 기업의 수익 구조를 바꾸는가?
2. 산업의 판도를 재편하는가?
3. 정책·금리·공급망 같은 거시 변수와 연결되는가?
```

세 질문 중 하나에도 답하기 어렵다면 `noise` 또는 `unclear`로 내려야 한다.

### 2.4 같은 뉴스도 국면에 따라 의미가 바뀐다

Autopark는 뉴스를 고정된 의미로 분류하면 안 된다. 같은 사실도 시장 국면에 따라 정반대로 해석될 수 있다.

| 시장 국면 | 같은 뉴스의 해석 |
|---|---|
| 성장 초입 | 대규모 투자, 공격적 가이던스, CAPEX 확대가 미래 확장의 신호로 읽힘 |
| 과열/고평가 | 같은 투자가 비용 부담, 마진 훼손, 자본효율성 악화로 읽힘 |
| 인플레이션 우려 | 강한 고용/소비가 금리 인상 우려로 악재가 될 수 있음 |
| 경기침체 우려 + 금리인하 기대 | 약한 고용/소비가 금리인하 가능성으로 호재가 될 수 있음 |
| 실적 기대 낮음 | 작은 서프라이즈도 강한 주가 반응을 만들 수 있음 |
| 실적 기대 높음 | 좋은 숫자도 “기대만큼 좋지 않다”로 해석될 수 있음 |

따라서 모든 스토리라인은 `market_regime` 필드를 가져야 한다.

```yaml
market_regime:
  dominant_narrative: null        # AI optimism | rate-cut hope | inflation fear | recession fear | earnings optimism | valuation concern | policy shock | other
  risk_appetite: null             # risk_on | risk_off | mixed | unclear
  expectation_level: null         # low | normal | high | extreme | unclear
  valuation_sensitivity: null     # low | medium | high
  rate_sensitivity: null          # low | medium | high
```

### 2.5 시장은 공식 발표보다 먼저 움직인다

선반영 판단은 첫 꼭지 선정에서 매우 중요하다. 공식 발표가 “좋다/나쁘다”보다 중요한 것은 **이미 가격에 반영된 기대와, 아직 반영되지 않은 새 변수의 차이**다.

```text
공식 발표 = 후행 확인일 수 있음
가격 움직임 = 기대 변화의 선행 반응일 수 있음
첫 꼭지 = 발표 내용 자체보다 “기대가 어떻게 바뀌었는가”를 설명해야 함
```

선반영을 볼 때는 다음 네 가지를 같이 본다.

| 요소 | 질문 |
|---|---|
| 인과관계 | 이 뉴스가 실제 가격 반응을 설명하는가, 아니면 사후 해석인가? |
| 시장 메커니즘 | 금리, 유동성, 할인율, 컨센서스, 포지션 변화와 연결되는가? |
| 정보 접근 구조 | 주요 기관/애널리스트가 이미 알고 있던 정보인가, 새 정보인가? |
| 기대 형성 | 시장 참여자의 공통 기대가 어느 정도까지 올라와 있었는가? |

---

## 3. 첫 꼭지 선정의 기본 원칙

### 3.1 첫 꼭지는 “가장 흥미로운 뉴스”가 아니라 “오늘 시장을 가장 잘 설명하는 뉴스”다

첫 꼭지 후보는 아래 네 가지를 동시에 만족할수록 강하다.

```text
시장 원인성: 오늘 가격 움직임을 설명한다.
구조적 영향: 펀더멘털·금리·정책·산업 구조에 영향을 준다.
기대 변화: 기존 컨센서스나 내재 기대를 바꾼다.
방송 적합성: 첫 5분 안에 청자가 이해할 수 있다.
```

단순히 많이 언급된 이슈, 조회수가 높을 것 같은 이슈, X에서 뜨거운 이슈는 첫 꼭지의 필요조건이 아니다. 이들은 `attention_signal`일 뿐이다.

### 3.2 첫 꼭지 승격 조건

아래 조건 중 5개 이상을 만족하면 첫 꼭지 후보로 승격할 수 있다.

| 코드 | 조건 | 설명 |
|---|---|---|
| `L1_market_causality` | 지수·금리·달러·유가·섹터·대형주 반응과 연결됨 | 사후 해석이 아니라 가격 반응의 원인 후보여야 함 |
| `L2_multi_source_repetition` | 주요 소스 다수에서 반복됨 | 관심도 신호. 단, 이것만으로는 부족 |
| `L3_structural_impact` | 수익 구조, 산업 판도, 정책 경로, 금리 경로를 바꿈 | 신호의 핵심 |
| `L4_expectation_gap` | 기대 대비 결과 또는 내재 기대가 바뀜 | 실적/경제지표/가이던스에서 중요 |
| `L5_forward_view` | 앞으로 볼 데이터나 이벤트가 명확함 | 방송 마무리와 연결 가능 |
| `L6_visual_anchor` | 한 장면으로 보여줄 차트/히트맵/표/헤드라인이 있음 | 장표화 가능성 |
| `L7_viewer_relevance` | 위폴 시청자가 오늘 바로 궁금해할 만함 | 방송 적합성 |
| `L8_korea_open_relevance` | 한국장/국내 투자자 관찰 포인트와 연결됨 | 제품 목적상 추가 기준 |
| `L9_counterpoint_ready` | 반론과 판단 수정 조건을 제시할 수 있음 | 과잉 확신 방지 |

### 3.3 첫 꼭지 배제 조건

아래 중 하나라도 해당하면 원칙적으로 첫 꼭지에서 제외한다.

| 배제 코드 | 설명 | 예외 |
|---|---|---|
| `D1_unverified_only` | 공식 자료나 신뢰 가능한 매체 확인 없이 루머만 있음 | 루머 자체가 시장을 크게 흔든 경우 `sentiment_shock`로 보조 처리 |
| `D2_sentiment_only` | X/Reddit 반응만 있고 가격·팩트·데이터가 없음 | 시장 심리 코너에서만 사용 |
| `D3_no_market_reaction` | 관련 자산 반응이 거의 없음 | 방송 전 선제 프리뷰라면 `watch_only` 가능 |
| `D4_already_priced_no_new_info` | 이미 알려진 이슈의 반복 보도 | 새 수치/가이던스/정책 변화가 있으면 재평가 |
| `D5_too_complex_for_opening` | 첫 5분에 이해시키기 어려움 | 보조 꼭지 또는 백업 자료 |
| `D6_low_visual_or_talk_value` | 보여줘도, 말해도 이해가 빨라지지 않음 | 내부 리서치용으로 보류 |
| `D7_duplicate_of_stronger_story` | 더 강한 스토리라인에 흡수 가능 | 병합 처리 |

---

## 4. 시그널/노이즈 판정 체계

### 4.1 4단계 분류

Autopark는 모든 후보에 대해 하나의 분류를 부여한다.

| 분류 | 의미 | 사용 방식 |
|---|---|---|
| `signal` | 시장/기업/산업/정책 경로에 구조적 영향을 줄 가능성이 높음 | 첫 꼭지 또는 핵심 스토리라인 후보 |
| `mixed` | 구조적 요소와 단기 심리가 섞여 있음 | 반론과 관찰 포인트 필수 |
| `noise` | 단기 변동성 또는 관심도는 있으나 본질 영향이 약함 | 보조/드롭/심리 온도계 |
| `unclear` | 정보가 부족하거나 시장 반응이 아직 확인되지 않음 | watch-only, 추가 확인 필요 |

### 4.2 시그널 판정 질문

```yaml
signal_questions:
  - id: SQ1
    question: "기업의 매출·이익·현금흐름·마진·시장지배력 중 하나를 바꾸는가?"
  - id: SQ2
    question: "산업의 경쟁구도, 수익모델, 수요곡선, 공급망을 바꾸는가?"
  - id: SQ3
    question: "금리·통화정책·물가·고용·소비·성장률 경로를 바꾸는가?"
  - id: SQ4
    question: "정책·규제·관세·보조금·세금으로 비용이나 수요가 달라지는가?"
  - id: SQ5
    question: "대형주/핵심 기업의 실적이 섹터 또는 지수 방향성을 재평가하게 하는가?"
  - id: SQ6
    question: "시장이 기존에 가격에 반영한 기대를 수정하게 만드는가?"
```

판정 규칙:

```text
- SQ 2개 이상이 yes이고 가격 반응이 있으면 signal 가능성이 높다.
- SQ 1개만 yes이고 데이터가 약하면 mixed로 둔다.
- SQ가 모두 no이면 noise로 둔다.
- SQ가 yes여도 출처가 약하면 unclear로 둔다.
```

### 4.3 노이즈 판정 질문

```yaml
noise_questions:
  - id: NQ1
    question: "이미 시장이 오래 알고 있던 이슈의 반복인가?"
  - id: NQ2
    question: "공식 확인 없는 루머인가?"
  - id: NQ3
    question: "발언은 강하지만 실제 정책·수익모델·현금흐름 변화가 없는가?"
  - id: NQ4
    question: "가격 반응이 짧고 특정 소형주/테마주에만 제한되는가?"
  - id: NQ5
    question: "시장 심리에는 영향을 주지만 미래 이익에는 연결되지 않는가?"
  - id: NQ6
    question: "같은 테마의 더 강한 근거가 이미 다른 스토리라인에 있는가?"
```

판정 규칙:

```text
- NQ 2개 이상이 yes이면 noise 가능성이 높다.
- NQ1이 yes라도 새 정책/숫자/가이던스가 있으면 mixed로 재평가한다.
- NQ2가 yes이면 첫 꼭지 금지. 가격 충격이 큰 경우에도 sentiment_shock로만 처리한다.
```

---

## 5. 기대 대비 결과 판단 기준

### 5.1 기대는 세 층으로 나눈다

실적이나 경제지표를 판단할 때 “컨센서스를 상회/하회”만으로는 부족하다. Autopark는 기대를 세 층으로 분리해야 한다.

| 기대 층위 | 의미 | 데이터 후보 |
|---|---|---|
| `official_consensus` | 애널리스트 평균 전망치, 공식 컨센서스 | EPS/매출 컨센서스, CPI 전망치, 고용 전망치 |
| `whisper_or_stretched_expectation` | 시장 참여자가 실제로 내심 기대한 더 높은/낮은 수준 | 주가 랠리, 옵션/포지션, X/애널리스트 톤, 밸류에이션 프리미엄 |
| `priced_in_expectation` | 가격에 이미 반영된 기대 | 발표 전 주가/섹터/금리/달러 움직임, 멀티플 확장, FedWatch 변화 |

방송에서 중요한 것은 다음 문장이다.

```text
결과가 좋았는가?보다, 시장이 이미 어느 정도를 기대하고 있었고 이번 결과가 그 기대를 바꾸었는가?
```

### 5.2 기대 대비 결과 매트릭스

| 결과 | 기대 수준 | 시장 반응 가능성 | 해석 |
|---|---|---|---|
| 좋음 | 낮음 | 강한 상승 가능 | 새로운 기대 형성 |
| 좋음 | 보통 | 상승 또는 안정 | 컨센서스 확인 |
| 좋음 | 매우 높음 | 무반응 또는 하락 가능 | 이미 선반영, 더 큰 서프라이즈 필요 |
| 나쁨 | 낮음 | 제한적 하락 또는 반등 | 최악은 피했다는 해석 가능 |
| 나쁨 | 보통 | 하락 가능 | 기대 훼손 |
| 나쁨 | 매우 높음 | 큰 하락 가능 | 높은 밸류에이션/기대 붕괴 |
| 혼재 | 불명확 | 변동성 확대 | 가이던스와 어닝콜 톤이 중요 |

### 5.3 실적 발표 전용 체크리스트

실적 관련 스토리라인은 반드시 아래 필드를 채워야 한다.

```yaml
earnings_expectation_map:
  ticker: null
  event_time: null             # pre-market | after-market | regular-hours | unknown
  official_consensus:
    revenue: null
    eps: null
    margin: null
    guidance: null
  actual_result:
    revenue: null
    eps: null
    margin: null
    guidance: null
  gap_vs_consensus:
    revenue: null
    eps: null
    margin: null
    guidance: null
  pre_event_price_action:
    stock: null
    sector: null
    index: null
    multiple_expansion: null
  implied_expectation_level: null   # low | normal | high | extreme | unclear
  management_tone:
    demand: null
    margin: null
    capex: null
    ai_or_growth: null
    cost_or_risk: null
  market_interpretation: null
  why_stock_moved: null
```

품질 규칙:

```text
- 실적 스토리라인에 consensus/actual/guidance 중 아무것도 없으면 signal 판정 금지.
- “실적이 좋았는데 주가가 하락”한 경우 expectation_gap 또는 guidance_disappointment를 반드시 검토한다.
- 대형 기업 실적은 개별 종목 이슈가 아니라 섹터/경기 지표로도 평가한다.
- 어닝콜의 표현 변화는 숫자만큼 중요할 수 있으므로 tone 필드를 분리한다.
```

### 5.4 경제지표 전용 체크리스트

경제지표 관련 스토리라인은 단순히 수치가 좋고 나쁜지가 아니라, **연준의 금리 경로와 시장의 현재 관심사**에 맞춰 해석해야 한다.

```yaml
macro_expectation_map:
  indicator: null              # CPI | PCE | PPI | NFP | unemployment | retail_sales | ISM | GDPNow | other
  official_consensus: null
  actual_result: null
  prior_result: null
  surprise_direction: null     # stronger | weaker | inline | mixed
  fed_path_implication: null   # more_hawkish | more_dovish | neutral | unclear
  market_regime_context: null  # inflation_fear | recession_fear | rate_cut_hope | soft_landing | other
  market_reaction:
    us10y: null
    dxy: null
    sp500: null
    nasdaq: null
    usdkrw: null
  interpretation: null
```

품질 규칙:

```text
- 고용/물가 지표는 “좋다/나쁘다”보다 “현재 시장이 무엇을 기다리는가”로 해석한다.
- 인플레이션 우려 국면에서는 강한 데이터가 악재가 될 수 있다.
- 금리인하 기대 국면에서는 약한 데이터가 호재가 될 수 있다.
- 지표 발표 전 프리뷰는 첫 꼭지보다 watch-only 또는 what_to_watch가 적합하다.
```

---

## 6. 선반영 판단 기준

### 6.1 선반영 여부를 판단하는 질문

```yaml
prepricing_questions:
  - id: P1
    question: "이 이벤트 전 주가/섹터/지수/금리/달러가 이미 같은 방향으로 움직였는가?"
  - id: P2
    question: "컨센서스보다 더 높은 내재 기대가 형성되어 있었는가?"
  - id: P3
    question: "밸류에이션 멀티플이 이미 확장되어 있었는가?"
  - id: P4
    question: "옵션/포지션/애널리스트 톤이 한쪽으로 쏠려 있었는가?"
  - id: P5
    question: "공식 발표가 새 정보라기보다 기존 기대의 확인에 가까운가?"
  - id: P6
    question: "발표 후 주가 반응이 숫자보다 가이던스/미래 기대에 더 민감했는가?"
```

판정 규칙:

```text
- P1+P2+P3 중 2개 이상 yes이면 `high_prepricing_risk`.
- P5가 yes이고 새 변수 없음이면 `confirmation_news`.
- P6가 yes이면 실적 숫자보다 guidance/tone 중심으로 설명한다.
```

### 6.2 선반영 리스크 라벨

| 라벨 | 의미 | 방송 해석 |
|---|---|---|
| `low_prepricing` | 기대가 낮거나 가격 반영이 약함 | 서프라이즈가 강하게 작동 가능 |
| `normal_prepricing` | 컨센서스 수준의 기대 반영 | 결과와 가이던스를 균형 있게 봄 |
| `high_prepricing` | 주가·멀티플·심리가 이미 높음 | 좋은 결과도 약하게 반응할 수 있음 |
| `extreme_prepricing` | 모두가 같은 방향을 기대 | 첫 꼭지는 “기대 과열과 차익실현 리스크”가 될 수 있음 |
| `unknown_prepricing` | 데이터 부족 | 단정 금지, watch-only |

### 6.3 “좋은 뉴스인데 하락” 설명 템플릿

```text
표면적으로는 좋은 결과였지만, 시장은 이미 더 높은 수준을 가격에 반영하고 있었다. 이번 발표는 컨센서스는 넘었지만 내재 기대를 충분히 높이지 못했고, 특히 가이던스/마진/수요 전망에서 추가 확신을 주지 못했다. 그래서 주가는 숫자가 아니라 기대와 현실의 차이를 거래했다.
```

### 6.4 “나쁜 뉴스인데 상승” 설명 템플릿

```text
숫자만 보면 부정적이지만, 시장은 이미 더 나쁜 시나리오를 반영하고 있었다. 이번 결과는 최악의 우려를 확인하지 않았고, 동시에 금리·정책·가이던스 측면에서 앞으로의 부담이 줄어들 수 있다는 해석을 만들었다. 그래서 악재가 완화 신호로 받아들여졌다.
```

---

## 7. 뉴스 반응 속도와 국면 판단

### 7.1 정책 뉴스와 기업 뉴스는 반응 속도가 다르다

| 뉴스 유형 | 반응 속도 | 판단 포인트 | Autopark 처리 |
|---|---|---|---|
| 정책/규제/관세 | 단계적으로 진화 | 발표보다 구체화 과정, 비용 계산, 2차 효과 | `policy_path_watch` 필드 필요 |
| 금리/Fed | 즉각 + 장기 영향 | 할인율, 유동성, 밸류에이션 전반 | 첫 꼭지 후보 우선순위 높음 |
| 경제지표 | 즉각 반응하되 국면 의존 | 시장이 인플레를 걱정하는지 침체를 걱정하는지 | `market_regime_context` 필수 |
| 기업 실적 | 즉각 반응 | 핵심 펀더멘털, 컨센서스, 가이던스, 어닝콜 톤 | `earnings_expectation_map` 필수 |
| 개별 기업 뉴스 | 매우 빠름 | 그 기업의 생명선을 건드리는지 | 업종별 핵심 지표 필요 |
| 소셜/루머 | 매우 빠르지만 약함 | 팩트 검증 전까지 변동성만 유발 | `sentiment_only` 또는 `unclear` |

### 7.2 정책 뉴스용 단계 평가

정책 뉴스는 발표 당일의 헤드라인보다 구체화 과정이 더 중요할 수 있다.

```yaml
policy_path_watch:
  policy_topic: null
  stage: proposal | announcement | clarification | implementation | market_repricing | rollback_or_delay | unknown
  cost_channels:
    - corporate_margin
    - consumer_price
    - supply_chain
    - fiscal_deficit
    - trade_flow
    - liquidity
  affected_sectors: []
  market_reaction_so_far: []
  next_policy_milestone: null
```

운영 규칙:

```text
- 정책 뉴스는 첫 보도만으로 결론 내리지 않는다.
- 비용이 어느 기업/섹터/소비자에게 전가되는지 계산할 수 있을 때 시그널 강도가 올라간다.
- 시장이 처음에는 긍정적으로 받아들였더라도, 구체화 과정에서 악재로 재평가될 수 있다.
```

### 7.3 업종별 생명선 판단

기업 뉴스는 해당 기업/업종의 핵심 펀더멘털을 건드릴 때만 강한 시그널이 된다.

| 업종/테마 | 생명선 예시 | 강한 시그널 예시 |
|---|---|---|
| AI 반도체 | 수요 지속성, 총마진, 공급능력, 경쟁우위 | 마진 변화, 고객 수요 전망, 대규모 수주, 경쟁사 위협 |
| 빅테크 플랫폼 | 광고/클라우드 성장, 비용 효율, 규제, AI 경쟁력 | CAPEX 부담, 광고 둔화, 규제 구체화, AI 제품 성과 |
| 전기차/자율주행 | 인도량, 마진, 가격 정책, FSD/로보틱스 기대 | 가격 인하 압박, 수요 둔화, 신사업 일정 변화 |
| 소비/유통 | 소비 체력, 재고, 마진, 가이던스 | 소비 둔화, 가격 전가 실패, 연말 수요 변화 |
| 금융 | 순이자마진, 신용손실, 예금 유출, 규제 | 연체율 상승, 유동성 스트레스, 자본규제 변화 |
| 헬스케어/바이오 | 임상 결과, 승인, 보험 적용, 시장 규모 | 임상 성공/실패, 적응증 확장, 보험 급여 변화 |
| 에너지 | 유가, 생산량, 지정학, CAPEX | 공급 충격, OPEC 정책, 원유 재고 변화 |

---

## 8. 리드 스토리 점수 모델 v0.1

### 8.1 점수 구조

`lead_score.total`은 100점 만점으로 계산한다. 이 점수는 모델 내부 기준이며, Notion 화면에는 원점수를 노출하지 않는 것을 권장한다. 사용자 화면에는 별점 또는 추천 문장으로 변환한다.

| 항목 | 배점 | 설명 |
|---|---:|---|
| `market_causality` | 20 | 오늘 가격 반응을 설명하는 정도 |
| `structural_signal` | 20 | 펀더멘털·정책·금리·산업 구조 영향 |
| `expectation_gap` | 15 | 컨센서스/내재 기대/선반영 대비 새 변화 |
| `breadth_and_contagion` | 10 | 개별 종목을 넘어 섹터/지수/한국장으로 확산 가능성 |
| `evidence_quality` | 10 | 신뢰 출처, 공식 데이터, 숫자, 가격 반응의 품질 |
| `broadcast_fit` | 15 | 첫 5분 설명 가능성, 훅, 시각 자료, 시청자 relevance |
| `timing_urgency` | 10 | 오늘 반드시 다뤄야 하는 시의성 |

### 8.2 세부 채점 규칙

```yaml
lead_score_components:
  market_causality:
    0: "가격 반응과 연결 불명확"
    5: "일부 자산과 약하게 연결"
    10: "관련 종목/섹터 반응 확인"
    15: "지수 또는 핵심 자산 반응과 연결"
    20: "오늘 시장 전체 움직임의 주요 원인으로 설명 가능"
  structural_signal:
    0: "본질 영향 없음"
    5: "단기 심리 영향 중심"
    10: "기업/섹터 일부 영향"
    15: "실적·금리·정책 경로에 영향"
    20: "시장/산업/정책 방향을 재평가하게 함"
  expectation_gap:
    0: "기대 대비 변화 없음"
    5: "컨센서스 확인 수준"
    10: "컨센서스와 일부 괴리"
    15: "내재 기대 또는 선반영 수준을 크게 수정"
  breadth_and_contagion:
    0: "개별 소형 이슈"
    5: "관련 종목 몇 개로 확산"
    10: "섹터·지수·한국장 관찰 포인트로 확산"
  evidence_quality:
    0: "루머/소셜 단독"
    5: "기사 확인은 있으나 숫자 약함"
    10: "신뢰 출처 + 숫자 + 시장 반응 확인"
  broadcast_fit:
    0: "방송에서 설명하기 어려움"
    5: "보조 꼭지 가능"
    10: "핵심 꼭지 가능"
    15: "첫 5분 오프닝에 적합하고 그림/훅 있음"
  timing_urgency:
    0: "오늘 다룰 필요 낮음"
    5: "오늘 언급 가치 있음"
    10: "오늘 첫 꼭지로 다루지 않으면 늦음"
```

### 8.3 별점 변환

| 총점 | 내부 판정 | Notion 표시 |
|---:|---|---|
| 85~100 | 강력한 첫 꼭지 후보 | ★★★★★ |
| 70~84 | 첫 꼭지 또는 2번 꼭지 후보 | ★★★★ |
| 55~69 | 보조 스토리라인 | ★★★ |
| 40~54 | 언급/보류 | ★★ |
| 0~39 | drop 또는 watch-only | ★ |

### 8.4 신뢰도는 점수와 분리한다

점수가 높아도 출처가 약하면 첫 꼭지로 올리면 안 된다. 따라서 `confidence`를 별도 표시한다.

```yaml
confidence:
  level: high | medium | low
  basis:
    - official_data
    - tier1_media
    - market_price_reaction
    - multiple_independent_sources
    - social_only
    - inferred_by_model
```

운영 규칙:

```text
- lead_score >= 85라도 confidence가 low이면 rank 1 금지.
- social_only는 confidence high가 될 수 없다.
- 모델 추론만으로 핵심 원인을 확정하지 않는다. 반드시 evidence item_id를 연결한다.
```

---

## 9. Autopark 출력 스키마 보강안

### 9.1 Storyline 객체 보강

```json
{
  "storyline_id": "string",
  "rank": 1,
  "recommendation_stars": 5,
  "lead_score": {
    "total": 0,
    "components": {
      "market_causality": 0,
      "structural_signal": 0,
      "expectation_gap": 0,
      "breadth_and_contagion": 0,
      "evidence_quality": 0,
      "broadcast_fit": 0,
      "timing_urgency": 0
    },
    "confidence": "high | medium | low",
    "disqualifiers": []
  },
  "signal_assessment": {
    "classification": "signal | mixed | noise | unclear",
    "signal_axes": ["rates_signal", "macro_signal", "earnings_signal", "policy_signal"],
    "noise_flags": [],
    "structural_impact_summary": "string",
    "why_not_noise": "string",
    "what_would_make_it_noise": "string"
  },
  "expectation_assessment": {
    "official_consensus": "string | null",
    "implied_expectation": "low | normal | high | extreme | unclear",
    "prepricing_risk": "low_prepricing | normal_prepricing | high_prepricing | extreme_prepricing | unknown_prepricing",
    "actual_or_new_information": "string | null",
    "gap_summary": "string",
    "guidance_or_forward_view": "string | null"
  },
  "market_regime": {
    "dominant_narrative": "string",
    "risk_appetite": "risk_on | risk_off | mixed | unclear",
    "expectation_level": "low | normal | high | extreme | unclear",
    "rate_sensitivity": "low | medium | high",
    "valuation_sensitivity": "low | medium | high"
  },
  "lead_candidate_reason": "string",
  "hook": "string",
  "why_now": "string",
  "core_argument": "string",
  "counterpoint": "string",
  "what_would_change_my_mind": "string",
  "visual_vs_talk_role": {
    "mode": "visual_anchor | talk_only | visual_support",
    "visual_item_id": "string | null",
    "why": "string"
  },
  "evidence_to_use": [
    {
      "item_id": "string",
      "evidence_role": "fact_anchor | market_reaction | key_number | expectation_data | sentiment_confirmation | visual_anchor",
      "why_used": "string"
    }
  ],
  "evidence_to_drop": [
    {
      "item_id": "string",
      "drop_code": "already_known | weak_market_reaction | sentiment_only | duplicate_theme | insufficient_data | too_complex_for_opening | low_visual_value",
      "why_dropped": "string"
    }
  ]
}
```

### 9.2 `market-radar.json` 후보 객체 보강

`editorial-brief` 이전 단계에서 최소한 아래 필드를 만들어두면 편집장 판단이 안정된다.

```json
{
  "item_id": "string",
  "topic_cluster_id": "string",
  "source_type": "tier1_media | official | market_data | x | reddit | other",
  "asset_links": {
    "indices": [],
    "sectors": [],
    "single_names": [],
    "rates_fx_commodities": []
  },
  "initial_driver_type": "rates | macro | earnings | policy | sector_rotation | sentiment | other",
  "key_numbers": [],
  "price_reaction": [],
  "expectation_clues": [],
  "possible_noise_flags": [],
  "possible_signal_axes": [],
  "visual_candidate": true,
  "needs_fact_check": false
}
```

---

## 10. Notion 대시보드 카드 구성

2번 기준서를 반영한 첫 화면/스토리라인 카드는 아래 순서가 적합하다.

```text
[Lead Storyline]
1. 왜 첫 꼭지인가?
2. 시그널/노이즈 판정
3. 기대 대비 무엇이 달라졌나?
4. 시장은 이미 무엇을 선반영했나?
5. 어떤 자산이 어떻게 반응했나?
6. 방송에서 보여줄 자료 / 말로 처리할 자료
7. 반론과 판단 수정 조건
8. 다음에 볼 데이터
```

### 10.1 리드 스토리 카드 템플릿

```markdown
## 🥇 첫 꼭지 후보: {title}

**왜 첫 꼭지인가**
{lead_candidate_reason}

**판정**
- Signal/Noise: `{classification}`
- Signal axes: `{signal_axes}`
- Prepricing risk: `{prepricing_risk}`
- Confidence: `{confidence}`

**기대 대비 변화**
{gap_summary}

**시장 반응**
{market_reaction_summary}

**보여줄 자료 / 말로 처리할 자료**
- Visual: {visual_anchor_or_none}
- Talk-only: {talk_only_points}

**반론**
{counterpoint}

**판단을 바꿀 조건**
{what_would_change_my_mind}

**다음에 볼 것**
{what_to_watch}
```

### 10.2 드롭 자료 카드 템플릿

```markdown
## 버린 자료 / 보류 자료

| item_id | 제목 | 분류 | 버린 이유 | 다시 볼 조건 |
|---|---|---|---|---|
| {item_id} | {title} | {drop_code} | {why_dropped} | {revive_condition} |
```

---

## 11. 품질 게이트 v0.1

`review_dashboard_quality.py` 또는 그에 준하는 품질 검수 스크립트에 아래 규칙을 추가한다.

```yaml
quality_gates:
  signal_noise_and_lead_selection:
    - id: SN-001
      name: "signal_assessment_required"
      rule: "모든 storylines[*]에 signal_assessment.classification이 있어야 함"
    - id: SN-002
      name: "lead_score_required"
      rule: "rank 1 스토리라인에는 lead_score.total과 components가 있어야 함"
    - id: SN-003
      name: "lead_reason_required"
      rule: "rank 1 스토리라인에는 lead_candidate_reason이 비어 있으면 실패"
    - id: SN-004
      name: "no_unverified_lead"
      rule: "disqualifiers에 D1_unverified_only가 있으면 rank 1 금지"
    - id: SN-005
      name: "no_sentiment_only_as_signal"
      rule: "sentiment_only 자료만으로 signal 판정 또는 rank 1이면 실패"
    - id: SN-006
      name: "signal_requires_structural_reason"
      rule: "classification=signal이면 structural_impact_summary 필수"
    - id: SN-007
      name: "earnings_story_requires_expectation_map"
      rule: "driver_type=earnings이면 expectation_assessment와 key_numbers 필수"
    - id: SN-008
      name: "macro_story_requires_regime_context"
      rule: "driver_type=macro이면 market_regime.dominant_narrative 필수"
    - id: SN-009
      name: "good_news_down_requires_prepricing_or_guidance"
      rule: "좋은 결과+하락 설명에는 high_prepricing 또는 guidance_disappointment 중 하나가 있어야 함"
    - id: SN-010
      name: "bad_news_up_requires_regime_explanation"
      rule: "나쁜 결과+상승 설명에는 market_regime_context 설명이 있어야 함"
    - id: SN-011
      name: "score_confidence_separation"
      rule: "lead_score.total이 높아도 confidence=low이면 rank 1 금지 또는 경고"
    - id: SN-012
      name: "drop_code_required"
      rule: "evidence_to_drop[*].drop_code가 없으면 경고"
    - id: SN-013
      name: "duplicate_theme_merge_check"
      rule: "동일 topic_cluster_id가 여러 storylines에 반복되면 병합 검토 경고"
    - id: SN-014
      name: "first_5min_fit_required"
      rule: "rank 1 스토리라인은 broadcast_fit 또는 hook이 비어 있으면 경고"
```

---

## 12. 편집장 프롬프트 삽입용 블록

아래 블록은 `build_editorial_brief.py`의 시스템 또는 developer 프롬프트에 삽입할 수 있는 형태다.

```text
Apply the Signal/Noise and Lead Selection Policy.

Your task is to decide what should lead the 07:20 KST morning broadcast. Do not select the most sensational item. Select the item that best explains today's market.

For every storyline candidate:
1. Classify it as signal, mixed, noise, or unclear.
2. Identify signal axes: rates, macro, earnings, policy, industry structure, market structure, or sentiment.
3. Identify noise flags: already known, unverified rumor, celebrity comment only, minor management noise, no fundamental link, sentiment only, duplicate theme.
4. Explain whether the item changes revenue, profit, cash flow, margins, market share, competition, policy path, rate path, or investor expectations.
5. Build an expectation assessment: official consensus, implied expectation, prepricing risk, actual/new information, gap summary, guidance/forward view.
6. Consider market regime. The same data can be good or bad depending on whether the market is worried about inflation, recession, valuation, policy, or earnings growth.
7. If an earnings story is included, do not stop at the reported numbers. Check consensus, pre-event price action, guidance, management tone, and why the stock moved.
8. If a macro story is included, explain the Fed-path implication and the reaction in rates, dollar, and equities.
9. Score each storyline using the 100-point lead_score model: market_causality, structural_signal, expectation_gap, breadth_and_contagion, evidence_quality, broadcast_fit, timing_urgency.
10. Keep confidence separate from score. A high score with low confidence cannot be the lead.
11. Rank the first storyline only if it has a clear lead_candidate_reason and no disqualifier such as unverified_only or sentiment_only.
12. For dropped items, provide a drop_code and a revive_condition.
13. Output language should be concise, spoken-Korean friendly, and usable by a morning broadcast host.
14. Avoid direct buy/sell instructions. Provide observation points and what to watch next.
```

---

## 13. 회고 루프에 넘길 라벨 후보

이 문서는 5단계 runbook 결합 전의 초안이다. 2번 기준서에서 회고에 넘겨야 할 라벨은 다음과 같다.

```yaml
retrospective_labels:
  lead_selection:
    - used_as_lead
    - used_later
    - mentioned_only
    - not_used
  lead_failure_reason:
    - wrong_market_driver
    - overestimated_signal
    - underestimated_noise
    - expectation_gap_missed
    - prepricing_missed
    - too_complex_for_opening
    - weak_visual_value
    - weak_viewer_relevance
    - better_story_emerged
    - source_gap
    - late_breaking_news
  signal_noise_accuracy:
    - true_signal
    - false_signal
    - true_noise
    - false_noise
    - mixed_but_used
    - unclear_but_important
  expectation_assessment:
    - consensus_gap_correct
    - consensus_gap_wrong
    - implied_expectation_correct
    - implied_expectation_missed
    - guidance_importance_correct
    - guidance_importance_missed
  prepricing_assessment:
    - prepricing_correct
    - prepricing_underestimated
    - prepricing_overestimated
    - confirmation_news_correct
    - confirmation_news_wrong
```

### 13.1 회고 질문

방송 후 자막/대시보드 비교에서 아래 질문을 남긴다.

```text
1. Autopark가 rank 1로 올린 소재가 실제 첫 꼭지로 쓰였는가?
2. 쓰이지 않았다면 이유는 시장 원인성, 시청자 relevance, 설명 난이도, 자료 부족 중 무엇인가?
3. signal로 분류한 이슈가 실제 방송에서도 구조적 이슈로 다뤄졌는가?
4. noise로 분류한 이슈가 실제로는 중요하게 쓰였는가?
5. 실적/지표 해석에서 컨센서스보다 내재 기대를 잘 읽었는가?
6. “좋은 뉴스인데 하락” 또는 “나쁜 뉴스인데 상승”을 설명할 때 선반영/국면 판단이 맞았는가?
7. 버린 자료 중 다시 살려야 했던 자료가 있었는가? 있었다면 revive_condition은 무엇인가?
```

---

## 14. 사람에게 확인하면 좋은 질문

박종훈 저자 또는 실제 제작진에게 확인하면 좋은 질문이다.

1. 첫 꼭지를 고를 때 `시장 설명력`과 `시청자 흥미도`가 충돌하면 어느 쪽을 우선하는가?
2. “이건 방송 첫 꼭지가 아니다”라고 판단하는 대표적 사례는 무엇인가?
3. 실적이 좋은데 주가가 빠지는 경우, 방송에서 어느 정도까지 밸류에이션/선반영을 설명하는가?
4. X에서 뜨거운 이슈지만 신뢰 출처가 약할 때, 아예 빼는가 아니면 심리 코너로 짧게 처리하는가?
5. 정책 뉴스는 발표 당일 다루는가, 구체화될 때 다시 다루는가?
6. 첫 5분에 쓰기 어려운 복잡한 이슈는 보조 꼭지로 넘기는가, 백업 장표로만 남기는가?
7. 한국장 연결성이 약하지만 미국장 설명력은 강한 이슈는 첫 꼭지가 될 수 있는가?
8. 방송 후 회고에서 “첫 꼭지 판단 성공”을 무엇으로 정의하는가?

---

## 15. 이번 문서의 결론

2번 기준서의 핵심은 다음이다.

```text
Autopark는 모든 후보 스토리라인에 대해 다음 순서로 판단한다.

1. 이 뉴스가 오늘 시장 가격 반응을 설명하는가?
2. 매출·이익·현금흐름·마진·시장점유율·경쟁구도·금리·정책 경로 중 무엇을 바꾸는가?
3. 이미 알려진 반복 뉴스인가, 새 정보인가?
4. 컨센서스와 내재 기대는 어디까지 올라와 있었는가?
5. 실제 결과 또는 새 정보가 그 기대를 어떻게 바꾸었는가?
6. 이미 가격에 선반영된 부분과 아직 반영되지 않은 변수는 무엇인가?
7. 같은 뉴스가 현재 국면에서는 호재인가 악재인가?
8. 첫 5분 안에 시청자에게 설명 가능한가?
9. 장표로 보여줄 가치가 있는가, 말로 처리하는 게 나은가?
10. 반론과 판단 수정 조건이 명확한가?
```

이 10개 질문을 안정적으로 통과한 소재만 첫 꼭지 후보가 된다. 나머지는 보조 꼭지, 심리 온도계, watch-only, drop으로 분리한다.
