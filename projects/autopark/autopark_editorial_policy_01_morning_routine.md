---
title: "Autopark Editorial Policy v1 — 01 Morning Routine"
version: "0.1-draft"
scope: "priority_1_morning_routine_core_questions_daily_thesis"
created_for: "슈카친구들 / 위폴 아침방송 자동화 대시보드"
source_basis:
  - "박종훈의 미국주식투자 레시피: 들어가는 말, pp.4-8"
  - "박종훈의 미국주식투자 레시피: 11장 하루 30분 루틴으로 시장을 꿰뚫다, pp.212-233"
repo_context:
  - "buykings/projects/autopark: 수집 → market-radar → editorial-brief → Notion → 품질검수 → 회고"
status: "draft_for_prompt_and_quality_gate_design"
---

# Autopark Editorial Policy v1 — 01. 박종훈식 아침 루틴 기준서

## 0. 한 문장 정의

Autopark의 1차 임무는 **뉴스를 많이 모아 요약하는 것**이 아니라, 아침 7:20 방송 진행자가 제한된 시간 안에 다음 결정을 내리도록 돕는 것이다.

> 오늘 미국장을 실제로 움직인 원인은 무엇이고, 그것을 어떤 자료와 어떤 순서로 방송에서 설명할 것인가?

따라서 Autopark는 `뉴스 요약기`가 아니라 `방송용 시장 판단 보조기`로 설계되어야 한다.

---

## 1. 이 문서의 범위

이 문서는 전체 기준서 중 **1번 우선순위**에 해당한다.

| 구분 | 포함 여부 | 설명 |
|---|---:|---|
| 박종훈식 아침 루틴 | 포함 | 새벽 시장 확인 → 반복 헤드라인 확인 → 자료 캡처 → 현지 시장 포인트 확인 → 방송 흐름 구성 |
| 핵심 질문 체계 | 포함 | 오늘 시장 원인, 핵심 메시지, 시그널/노이즈, 핵심 데이터, 한 장면, 전달 방식, 마무리 관점 |
| 하루 30분 뉴스 루틴 | 포함 | 키워드 스캔, 핵심 이슈 심층 분석, 심리 확인, 한두 줄 관점 정리 |
| Autopark 출력 스키마 | 포함 | `daily_thesis`, `market_drivers`, `storylines`, `evidence_to_use`, `visual_anchor` 등 |
| 소스별 세부 역할 | 제외 | 4장·5장 기준서에서 별도 작성 예정 |
| 시그널/노이즈 정량 점수 | 일부만 포함 | 기본 프리체크만 포함. 상세 스코어링은 2장·3장·10장 기준서에서 작성 예정 |
| 히트맵/실적/섹터 상세 규칙 | 제외 | 9장·10장 기준서에서 별도 작성 예정 |
| 회고 runbook 결합 | 일부만 포함 | 회고 필드 후보만 제안. 최종 결합 문서는 5단계에서 작성 예정 |

---

## 2. 책에서 추출한 운영 원칙

### 2.1 정보 수집보다 “판단 체계화”가 우선이다

11장의 핵심은 정보의 양이 아니다. 레거시 미디어, 뉴미디어, 리포트, 애널리스트 의견, 영향력 있는 인물의 발언은 모두 조각난 상태로 존재한다. 이를 그대로 소비하면 판단이 흐려질 수 있으므로, 진행자 관점의 **나만의 타임라인**으로 재구성해야 한다.

Autopark에 적용하면 다음과 같다.

```text
수집된 기사 100개를 보여주는 것 < 오늘 시장을 설명하는 3개 원인을 구조화하는 것
단순 요약 10개를 만드는 것 < 방송 첫 꼭지 후보 1개와 보조 꼭지 2~4개를 제안하는 것
출처별 뉴스를 나열하는 것 < 각 자료가 방송 판단에서 맡는 역할을 표시하는 것
```

### 2.2 시장 판단은 두 개의 상위 질문에서 출발한다

박종훈식 시장 정리의 상위 질문은 다음 두 가지로 운영형 변환할 수 있다.

1. **오늘 시장을 실제로 움직인 요인은 무엇인가?**
2. **그래서 앞으로 어떤 관점으로 대응해야 하는가?**

Autopark는 모든 후보 뉴스와 자료를 이 두 질문에 종속시켜야 한다. 후보가 흥미롭더라도 이 두 질문 중 하나에 기여하지 못하면, 첫 꼭지 또는 핵심 스토리라인 후보가 아니라 `supporting_material` 또는 `drop`으로 분류한다.

### 2.3 헤드라인의 반복은 “중복”이 아니라 “시장 관심도 신호”다

여러 주요 매체에서 같은 이슈가 반복되면, 이는 단순 중복이 아니라 그날 시장의 핵심 키워드일 가능성이 있다. 다만 반복 빈도만으로 첫 꼭지를 결정해서는 안 된다. 반복 키워드는 다음 검증 단계를 통과해야 한다.

```text
반복 출현 → 시장 가격 반응 확인 → 숫자/데이터 확인 → 심리 반응 확인 → 방송 메시지화
```

### 2.4 숫자는 기사의 보조 정보가 아니라 스토리의 뼈대다

핵심 뉴스 2~3개를 깊게 볼 때는 실적, 가이던스, 경제지표, 부채 규모, 금리, 유가, 달러, 물가, 고용, 생산, 소비, 경기 성장률 같은 숫자를 반드시 기록해야 한다. Autopark는 `numbers`를 별도 필드로 추출하고, 숫자가 없는 주장은 낮은 신뢰도로 처리해야 한다.

### 2.5 심리는 사실 확인 이후에 붙인다

X, 경제 인플루언서, 애널리스트 반응은 매우 중요하지만, 사실 확인을 대체하지 않는다. 운영 순서는 다음과 같아야 한다.

```text
팩트 확인 → 시장 반응 확인 → 숫자 확인 → 심리/해석 확인 → 방송용 관점 정리
```

심리 자료는 다음 세 가지 역할 중 하나로 분류한다.

| 역할 | 설명 | 방송 활용 |
|---|---|---|
| `sentiment_confirmation` | 이미 확인된 이슈에 대해 시장이 어떻게 받아들이는지 보여줌 | 스토리라인의 분위기 보강 |
| `narrative_spread` | 특정 해석이 시장에서 빠르게 확산되는지 확인 | 훅 또는 반론에 활용 |
| `sentiment_only` | 팩트 근거는 약하지만 군중심리를 보여줌 | 첫 꼭지 근거로 사용 금지, 보조 코멘트로만 사용 |

### 2.6 최종 결과는 한두 줄로 압축되어야 한다

좋은 아침 브리프는 길이가 아니라 압축력이 중요하다. Autopark의 최종 산출물은 반드시 다음 형태의 `daily_thesis`를 포함해야 한다.

```text
[원인] 때문에 [시장 반응]이 나타났다. 다만 [반론/주의점] 때문에 오늘 방송에서는 [관점]으로 정리한다.
```

예시 형식:

```text
연준 인하 기대가 후퇴하며 장기금리가 올랐고, 기술주 부담이 커졌다. 다만 실적 기대가 유지되는 빅테크와 방어 섹터의 온도 차이를 함께 봐야 한다.
```

---

## 3. 박종훈식 아침 루틴의 Autopark 변환

### 3.1 책의 루틴을 제품 관점으로 추상화

책에 묘사된 루틴은 다음과 같이 추상화할 수 있다.

| 책의 행동 | 운영상 의미 | Autopark 변환 |
|---|---|---|
| 새벽에 미국 시장 상황을 빠르게 확인 | 전날 미국장의 결과를 먼저 파악 | `overnight_market_snapshot` 생성 |
| 뉴스 헤드라인을 훑고 많이 언급된 기사 확인 | 반복 키워드와 시장 관심사 추출 | `repeat_keywords`, `top_headline_clusters` 생성 |
| 방송 자료가 될 데이터/헤드라인 캡처 | 시각 자료 후보 선별 | `visual_candidates`, `headline_cards` 생성 |
| 이동 중 Bloomberg Live로 현지 포인트 확인 | 미국 현지 시장의 해석 톤 확인 | `us_local_angle`, `institutional_tone` 생성 |
| 사무실에서 생각 정리 후 PPT 제작 | 방송 순서와 장표화 판단 | `storyline_order`, `slide_candidate_order` 생성 |

### 3.2 Autopark 현재 실행 시간에 맞춘 루틴 매핑

현재 운영 목표가 05:05 KST 실행, 05:30 KST 대시보드 완성이라면, Autopark는 사람의 03:50 루틴을 다음처럼 기계 루틴으로 압축해야 한다.

| 단계 | 권장 시간 | Autopark 작업 | 생성물 |
|---|---:|---|---|
| 0. 환경 스냅샷 | 05:05~05:08 | 지수, 금리, 유가, 달러, 환율, 비트코인, 주요 경제일정 확인 | `market_environment` |
| 1. 반복 키워드 스캔 | 05:08~05:12 | 주요 매체 헤드라인, X, Biztoc류 헤드라인 묶음 확인 | `repeat_keywords`, `headline_clusters` |
| 2. 시장 반응 매칭 | 05:12~05:16 | Finviz/지수/섹터/특징주와 키워드 연결 | `market_reaction_map` |
| 3. 핵심 이슈 2~3개 심층화 | 05:16~05:22 | 숫자, 가이던스, 정책/실적/거시 변수 확인 | `storyline_candidates` |
| 4. 심리·해석 확인 | 05:22~05:25 | X, 애널리스트, 경제 인플루언서 반응 확인 | `sentiment_layer` |
| 5. 편집장 판단 | 05:25~05:30 | 첫 꼭지, 보조 꼭지, 버릴 자료, 한 줄 관점 생성 | `editorial_brief`, `notion_markdown` |

이 시간표의 핵심은 각 단계의 산출물이 다음 단계의 입력이 되도록 만드는 것이다. 예를 들어 `repeat_keywords`가 `market_reaction_map`과 연결되지 못하면, 그 키워드는 첫 꼭지 후보가 아니라 `watch_only`로 내려간다.

---

## 4. 아침방송 핵심 질문 체계

Autopark의 편집장 모델은 모든 후보 스토리라인에 대해 아래 질문을 순서대로 통과시켜야 한다.

| ID | 운영 질문 | 모델이 답해야 할 내용 | 관련 출력 필드 | 실패 시 처리 |
|---|---|---|---|---|
| Q1 | 오늘 시장을 움직인 원인은 무엇인가? | 가격 반응과 연결된 실제 원인 | `market_driver.claim` | 원인 불명확 시 `watch_only` |
| Q2 | 이 중 가장 중요한 메시지는 무엇인가? | 방송에서 반드시 남겨야 할 한 문장 | `core_message` | 메시지가 여러 개면 스토리라인 분리 또는 병합 |
| Q3 | 단기 소음인가, 가치 변화인가? | 펀더멘털·거시·정책·심리 중 어디에 속하는지 | `signal_or_noise_precheck` | 심리뿐이면 첫 꼭지 금지 |
| Q4 | 오늘 시장을 한 장면으로 보여준다면 무엇인가? | 히트맵, 금리 차트, FedWatch, 실적표, 기사 헤드라인 등 | `visual_anchor` | 그림으로 이해가 빨라지지 않으면 말로 처리 |
| Q5 | 시장을 지탱하거나 흔든 핵심 데이터는 무엇인가? | 숫자, 지표, 컨센서스 대비 차이, 가격 반응 | `key_numbers`, `supporting_data` | 숫자 없으면 주장 강도 하향 |
| Q6 | 어떻게 전달해야 지루하지 않은가? | 오프닝 훅, 쉬운 비유, 시청자 관점의 질문 | `hook`, `talk_track.opening` | 훅이 약하면 첫 꼭지 후보 하향 |
| Q7 | 마지막 시장 흐름을 어떻게 정리할 것인가? | 한두 줄 요약과 대응 관점 | `daily_thesis`, `closing_line` | 압축 실패 시 브리프 재생성 |
| Q8 | 앞으로 어떻게 대응해야 하는가? | 당장 매매 지시가 아니라 관찰 포인트와 리스크 | `forward_view`, `what_to_watch` | 과도한 투자 조언으로 흐르면 수정 |

---

## 5. 하루 30분 루틴의 시스템 설계

### 5.1 Stage 0 — 시장 환경을 가장 먼저 고정한다

11장은 금리, 유가, 달러, 경제지표를 가장 앞에 놓는 습관을 강조한다. 이는 개별 기업이 움직이는 “놀이터”의 상태를 확인하는 과정으로 볼 수 있다.

Autopark는 모든 스토리라인 생성 전에 다음 시장 환경을 고정해야 한다.

```yaml
market_environment:
  indices:
    sp500: null
    nasdaq: null
    dow: null
    russell2000: null
  rates:
    us10y: null
    us2y: null
    fedwatch_change: null
  macro_prices:
    dxy: null
    wti: null
    brent: null
    usdkrw: null
    bitcoin: null
  schedule:
    today_economic_events: []
    fomc_related_events: []
    earnings_key_events: []
  market_tone:
    risk_on_off: null
    dominant_pressure: null  # rates | earnings | policy | macro | geopolitics | sector_rotation | sentiment
```

품질 기준:

```text
- 스토리라인보다 시장 환경 카드가 먼저 생성되어야 한다.
- daily_thesis는 최소 1개 이상의 시장 환경 변수와 연결되어야 한다.
- 금리/달러/유가/지수 중 아무 변수와도 연결되지 않는 뉴스는 첫 꼭지 후보가 되기 어렵다.
```

### 5.2 Stage 1 — 오늘 시장을 움직인 키워드 파악

첫 단계는 헤드라인을 넓게 훑고 반복 키워드를 찾는 것이다. 주요 매체의 반복 출현, Biztoc류의 헤드라인 묶음, Finviz 지수·히트맵을 함께 본다.

```yaml
headline_scan:
  repeat_keywords:
    - keyword: null
      sources: []
      source_count: 0
      first_seen_at: null
      related_assets: []
      initial_importance: low  # low | medium | high
  headline_clusters:
    - cluster_id: null
      topic: null
      representative_headlines: []
      likely_driver_type: null
  finviz_snapshot:
    strong_sectors: []
    weak_sectors: []
    notable_single_names: []
    possible_market_scene: null
```

Stage 1의 판단 규칙:

```text
- 같은 이슈가 여러 매체에서 반복되면 `repeat_keyword`로 승격한다.
- 반복되지만 지수/섹터/금리/달러/유가 반응과 연결되지 않으면 `attention_only`로 둔다.
- Finviz에서 특정 섹터나 대형주 움직임이 두드러지면 관련 뉴스 클러스터와 매칭한다.
- 이 단계에서는 결론을 내리지 말고 후보군만 만든다.
```

### 5.3 Stage 2 — 핵심 이슈 2~3개를 깊게 본다

Stage 1에서 나온 후보 중 2~3개만 깊게 본다. 이 단계는 “요약”이 아니라 “스토리 구조화”다.

```yaml
issue_deep_dive:
  - issue_id: null
    topic: null
    key_numbers:
      - label: null
        value: null
        prior_or_consensus: null
        market_interpretation: null
    affected_assets:
      indices: []
      sectors: []
      single_names: []
      rates_fx_commodities: []
    fundamental_impact:
      company_revenue_profit_cashflow: null
      industry_structure: null
      policy_or_macro_path: null
    precheck_questions:
      affects_fundamentals: null
      changes_macro_path: null
      possibly_sentiment_noise: null
    provisional_classification: signal | noise | mixed | unclear
```

Stage 2의 판단 규칙:

```text
- 숫자가 있는 이슈를 우선한다.
- 숫자가 없는 해석은 보조 의견으로 처리한다.
- 핵심 이슈는 2~3개면 충분하다. 억지로 5개를 채우지 않는다.
- 기업 뉴스는 실적, 가이던스, 마진, 비용, 현금흐름, 수요 전망과 연결한다.
- 거시 뉴스는 금리 경로, 물가, 고용, 성장, 달러, 유가, 정책 일정과 연결한다.
```

### 5.4 Stage 3 — 시장 심리를 확인한다

이 단계는 객관적 사실을 확인한 뒤, 시장이 그 사실을 어떻게 받아들이는지 확인하는 단계다. X, 애널리스트, 경제 인플루언서, 실적 시즌의 종목별 반응을 활용한다.

```yaml
sentiment_layer:
  - issue_id: null
    institutional_reaction: null
    retail_reaction: null
    x_consensus_points: []
    disagreement_points: []
    sentiment_temperature: cold | neutral | warm | hot | euphoric | fearful
    sentiment_role: sentiment_confirmation | narrative_spread | sentiment_only
```

Stage 3의 판단 규칙:

```text
- X 반응은 팩트가 아니라 해석과 심리의 온도계다.
- 여러 신뢰 계정이 같은 포인트를 강조하면 `x_consensus_points`에 기록한다.
- 반응이 뜨겁지만 공식 기사/데이터/가격 반응이 약하면 `sentiment_only`로 제한한다.
- 감정이 과열된 이슈는 훅으로는 쓸 수 있지만, 첫 꼭지의 핵심 근거로는 쓰지 않는다.
```

### 5.5 Stage 4 — 한두 줄 관점으로 압축한다

마지막 단계는 전체 내용을 한두 줄로 압축하는 것이다. 경제 일정과 FOMC 일정도 함께 확인한 뒤, 그날 시장을 설명하는 `daily_thesis`를 만든다.

```yaml
summary_and_view:
  daily_thesis: null
  closing_line: null
  forward_view:
    base_case: null
    risk_case: null
    what_to_watch_next: []
  broadcast_angle:
    lead_storyline_id: null
    why_this_leads: null
    first_sentence: null
    transition_to_second_story: null
```

좋은 `daily_thesis`의 조건:

```text
- 원인과 시장 반응이 함께 들어간다.
- 최소 하나의 핵심 데이터 또는 가격 반응과 연결된다.
- 시청자가 오늘 한국장/미국장 관찰 포인트로 가져갈 수 있는 문장이어야 한다.
- 지나치게 투자 조언처럼 들리지 않고, 관찰 포인트 중심이어야 한다.
- 첫 꼭지와 마무리 멘트가 같은 방향을 가리켜야 한다.
```

---

## 6. Autopark 편집장 출력 계약

### 6.1 최소 출력 구조

`build_editorial_brief.py` 또는 그에 준하는 LLM 편집장 단계는 최소한 아래 구조를 산출해야 한다.

```json
{
  "daily_thesis": "",
  "market_environment": {
    "dominant_pressure": "rates | earnings | policy | macro | sector_rotation | sentiment | other",
    "risk_on_off": "risk_on | risk_off | mixed | unclear",
    "key_moves": []
  },
  "core_questions": {
    "what_moved_market": "",
    "core_message": "",
    "signal_or_noise_summary": "",
    "one_scene": "",
    "key_data": [],
    "delivery_angle": "",
    "closing_view": "",
    "forward_watch": []
  },
  "storylines": [
    {
      "storyline_id": "",
      "rank": 1,
      "recommendation_stars": 0,
      "lead_candidate_reason": "",
      "hook": "",
      "why_now": "",
      "core_argument": "",
      "signal_or_noise_precheck": "signal | noise | mixed | unclear",
      "driver_type": "rates | macro | earnings | policy | sector_rotation | sentiment | other",
      "key_numbers": [],
      "market_reaction": [],
      "visual_anchor": {
        "type": "heatmap | chart | table | headline | none",
        "item_id": "",
        "why_visual": ""
      },
      "talk_track": {
        "opening": "",
        "explain": "",
        "transition": "",
        "closing": ""
      },
      "counterpoint": "",
      "what_would_change_my_mind": "",
      "evidence_to_use": [],
      "evidence_to_drop": []
    }
  ],
  "dropped_materials": [
    {
      "item_id": "",
      "drop_reason": "",
      "drop_code": "already_known | weak_market_reaction | sentiment_only | too_complex_for_morning | low_visual_value | duplicate_theme | insufficient_data"
    }
  ]
}
```

### 6.2 필수 필드의 의미

| 필드 | 의미 | 생성 기준 |
|---|---|---|
| `daily_thesis` | 그날 시장을 한두 줄로 압축한 최종 관점 | Stage 4에서 생성 |
| `dominant_pressure` | 오늘 시장을 가장 크게 누른 또는 끌어올린 축 | 시장 환경 + 반복 키워드 + 가격 반응 |
| `what_moved_market` | 오늘 미국장을 움직인 핵심 원인 | 헤드라인이 아니라 가격 반응과 결합된 원인 |
| `core_message` | 방송이 끝난 뒤 시청자가 기억해야 할 메시지 | 첫 꼭지의 핵심 주장과 일치해야 함 |
| `one_scene` | 오늘 시장을 한 장면으로 보여줄 자료 | Finviz, 금리 차트, FedWatch, 실적표 등 |
| `lead_candidate_reason` | 왜 이 스토리라인이 첫 꼭지인지 | 원인성, 반복성, 시장 반응, 방송 적합성 |
| `signal_or_noise_precheck` | 상세 스코어링 전 기본 판정 | 2·3·10장 기준서에서 추후 정교화 |
| `what_would_change_my_mind` | 반론보다 강한 검증 조건 | 다음 데이터/가격 반응이 나오면 판단 수정 |

---

## 7. 첫 화면 대시보드 구성 기준

1번 기준서만 반영한 첫 화면은 아래 순서가 적합하다.

```text
[1] 오늘의 한 줄 관점 daily_thesis
[2] Overnight Market Environment
[3] 오늘 시장을 움직인 Top Drivers
[4] 첫 꼭지 후보 Lead Storyline
[5] 한 장면으로 보는 시장 One-scene Visual
[6] 핵심 숫자 Key Numbers
[7] 시장 심리 Sentiment Layer
[8] 버린 자료 / 보류 자료 Dropped or Watch-only
[9] 방송용 멘트 초안 Talk Track
[10] 다음에 볼 것 What to Watch
```

### 7.1 화면별 의도

| 카드 | 의도 | 있으면 안 되는 것 |
|---|---|---|
| 오늘의 한 줄 | 진행자가 방송 방향을 즉시 잡도록 함 | 중립적이고 무의미한 요약 |
| 시장 환경 | 개별 뉴스보다 먼저 시장의 배경을 고정 | 단순 지표 나열만 있고 해석 없음 |
| Top Drivers | 오늘 시장을 움직인 원인 후보 | 출처별 기사 목록 |
| Lead Storyline | 첫 꼭지 후보와 이유 | “흥미롭다” 수준의 추천 사유 |
| One-scene Visual | 오늘 시장을 한 장면으로 보여줌 | 관련은 있지만 설명력이 약한 이미지 |
| Key Numbers | 스토리를 지탱하는 숫자 | 숫자만 있고 의미 해석 없음 |
| Sentiment Layer | 시장이 이슈를 어떻게 받아들이는지 표시 | X 반응을 사실 근거처럼 사용 |
| Dropped / Watch-only | 버린 이유를 기록해 모델 학습에 사용 | “약함” 같은 모호한 제외 사유 |
| Talk Track | 방송에서 바로 말할 수 있는 순서 | 기사체 문장, 장황한 문단 |
| What to Watch | 다음 확인 지표·이벤트 | 매매 지시처럼 보이는 문장 |

---

## 8. 품질 게이트 v0.1

`review_dashboard_quality.py` 또는 그에 준하는 품질 검수 스크립트에 아래 규칙을 추가한다.

```yaml
quality_gates:
  morning_routine:
    - id: MR-001
      name: "daily_thesis_required"
      rule: "daily_thesis가 비어 있으면 실패"
    - id: MR-002
      name: "daily_thesis_has_cause_and_reaction"
      rule: "daily_thesis에 원인과 시장 반응이 모두 있어야 함"
    - id: MR-003
      name: "market_environment_before_storylines"
      rule: "시장 환경 요약 없이 스토리라인만 있으면 경고"
    - id: MR-004
      name: "lead_storyline_reason_required"
      rule: "rank 1 스토리라인에는 lead_candidate_reason이 필수"
    - id: MR-005
      name: "key_numbers_required_for_signal"
      rule: "signal로 분류된 스토리라인에는 key_numbers 또는 market_reaction 중 하나 이상 필요"
    - id: MR-006
      name: "sentiment_not_fact"
      rule: "sentiment_only 자료가 fact evidence로 쓰이면 실패"
    - id: MR-007
      name: "one_scene_visual_or_reason"
      rule: "visual_anchor가 없으면 왜 말로 처리하는지 reason 필요"
    - id: MR-008
      name: "max_storyline_focus"
      rule: "추천 스토리라인은 3~5개. 약한 후보를 억지로 채우면 경고"
    - id: MR-009
      name: "closing_matches_thesis"
      rule: "closing_line이 daily_thesis와 방향이 충돌하면 실패"
    - id: MR-010
      name: "no_direct_trading_instruction"
      rule: "매수/매도 지시처럼 보이는 문장은 경고 또는 실패"
```

---

## 9. 편집장 프롬프트 삽입용 블록

아래 블록은 `build_editorial_brief.py`의 시스템 또는 developer 프롬프트에 삽입할 수 있는 형태다.

```text
You are the morning broadcast editorial assistant for Wepoll.
Your job is not to summarize every collected item. Your job is to help the host decide what explains today's U.S. market and how to present it at 07:20 KST.

Follow the Morning Routine Policy:

1. Start from the market environment: major indices, rates, dollar, oil, FX, bitcoin, major economic/FOMC/earnings schedule.
2. Identify repeated keywords across major sources. Treat repetition as a market-attention signal, not as sufficient evidence.
3. Match repeated keywords to actual market reactions: indices, sectors, single names, rates, FX, commodities.
4. Select only 2-3 issues for deep analysis before recommending 3-5 storylines. Do not fill weak storylines just to reach a target count.
5. Extract key numbers: earnings, guidance, economic indicators, debt, valuation, rate moves, sector moves, consensus gaps.
6. Classify each issue with a precheck: signal, noise, mixed, or unclear. Sentiment-only items cannot be used as factual anchors.
7. Use X and influencer reactions only as a sentiment layer after factual and market-reaction checks.
8. Produce a daily_thesis in 1-2 sentences. It must contain both cause and market reaction.
9. Choose one visual anchor only if it makes the market easier to understand. If no visual helps, mark it as talk-only and explain why.
10. For the rank-1 storyline, explicitly explain why it should lead the broadcast.
11. Provide a talk_track that can be spoken by the host: opening, explanation, transition, closing.
12. Avoid direct buy/sell instructions. Provide observation points and what to watch next.
```

---

## 10. 회고 루프에 넘길 필드 후보

이 문서는 5단계 runbook 결합 전의 초안이다. 그래도 1번 기준서에서 바로 회고에 남겨야 할 필드는 다음과 같다.

```yaml
retrospective_hooks:
  - field: "daily_thesis_used"
    question: "방송에서 대시보드의 daily_thesis가 실제로 쓰였는가?"
    values: ["used_as_is", "used_with_edit", "not_used"]
  - field: "lead_storyline_used"
    question: "rank 1 스토리라인이 첫 꼭지로 쓰였는가?"
    values: ["used_as_lead", "used_later", "mentioned_only", "not_used"]
  - field: "lead_storyline_failure_reason"
    question: "첫 꼭지로 쓰이지 않았다면 이유는 무엇인가?"
    values:
      - "too_complex_for_opening"
      - "weak_market_reaction"
      - "low_viewer_relevance"
      - "better_story_emerged"
      - "insufficient_visual"
      - "already_known"
      - "sentiment_only_false_positive"
  - field: "one_scene_visual_used"
    question: "추천한 한 장면 자료가 실제 장표/화면으로 쓰였는가?"
    values: ["used", "replaced", "talk_only", "not_used"]
  - field: "missed_market_driver"
    question: "방송에서 다뤘지만 대시보드가 놓친 시장 원인이 있었는가?"
    values: ["none", "source_gap", "weighting_error", "late_breaking", "human_editorial_choice"]
```

---

## 11. Autopark 코드/프롬프트 반영 우선순위

1번 기준서 기준으로는 아래 순서로 반영하는 것이 좋다.

| 우선순위 | 대상 | 작업 |
|---:|---|---|
| 1 | `build_editorial_brief.py` | `daily_thesis`, `lead_candidate_reason`, `signal_or_noise_precheck`, `visual_anchor`, `what_to_watch` 필드 추가 |
| 2 | `market-radar.json` 생성 단계 | `market_environment`, `repeat_keywords`, `market_reaction_map`을 명시적으로 분리 |
| 3 | 품질 게이트 | MR-001~MR-010 추가 |
| 4 | Notion 템플릿 | 첫 화면을 `daily_thesis → market environment → lead storyline → one-scene visual` 순서로 재배치 |
| 5 | 회고 스크립트 | `daily_thesis_used`, `lead_storyline_used`, `one_scene_visual_used` 라벨 추가 |

---

## 12. 아직 사람에게 확인해야 할 질문

박종훈 저자 또는 실제 방송 제작진에게 확인하면 좋은 질문이다.

1. 첫 꼭지를 고를 때 **시장 원인성**과 **시청자 흥미도**가 충돌하면 어느 쪽을 우선하는가?
2. 장표화할 자료와 말로만 처리할 자료를 나누는 체감 기준은 무엇인가?
3. 40~50장 PPT 중 실제 방송에서 반드시 필요한 장표와 백업 장표의 비율은 어느 정도인가?
4. Bloomberg Live 등 현지 해석을 들었을 때, 기존 판단을 바꾸는 대표적 상황은 무엇인가?
5. “오늘 시장을 한 장면으로 표현한다면”이라는 질문에서 가장 자주 선택되는 자료 유형은 무엇인가?
6. 방송 후 복기할 때 “대시보드가 잘했다”고 볼 기준은 첫 꼭지 적중인지, 누락 방지인지, 멘트화 용이성인지?
7. 위폴 시청자 관점에서 미국장 이슈를 한국장/국내 투자자 관찰 포인트로 연결하는 기본 규칙이 있는가?

---

## 13. 이번 문서의 결론

1번 기준서의 핵심은 다음이다.

```text
Autopark는 아침마다 다음 순서로 답해야 한다.

1. 시장 환경은 어떤가?
2. 여러 매체가 반복해서 말하는 키워드는 무엇인가?
3. 그 키워드가 실제 가격 반응과 연결되는가?
4. 깊게 볼 핵심 이슈 2~3개는 무엇인가?
5. 그 이슈는 숫자와 데이터로 뒷받침되는가?
6. 시장 심리는 그 이슈를 어떻게 받아들이는가?
7. 오늘 시장을 한 장면으로 보여주는 자료는 무엇인가?
8. 방송 첫 꼭지는 무엇이고, 왜 그것이 첫 꼭지인가?
9. 오늘 시장을 한두 줄로 압축하면 무엇인가?
10. 진행자는 앞으로 무엇을 지켜보라고 말해야 하는가?
```

이 10개 질문에 안정적으로 답하면, Autopark는 단순 뉴스 수집 자동화에서 **아침방송 편집 판단 보조 시스템**으로 한 단계 올라갈 수 있다.
