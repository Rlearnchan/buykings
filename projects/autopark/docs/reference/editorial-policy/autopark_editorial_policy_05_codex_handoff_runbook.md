---
title: "Autopark Editorial Policy v1 — 05 Codex Handoff & Broadcast Asset Runbook"
version: "0.1-draft"
scope: "priority_5_integrate_policies_code_prompt_visual_assets_retrospective"
created_for: "슈카친구들 / 위폴 아침방송 자동화 대시보드"
source_basis:
  - "01 Morning Routine 기준서"
  - "02 Signal/Noise & Lead Selection 기준서"
  - "03 Source Roles 기준서"
  - "04 Market Map, Heatmap, Sector, Fixed Checklist 기준서"
  - "실제 방송 샘플: 바이킹 0429.pptx + TXT.rtf"
  - "실제 방송 샘플: 바이킹 0430.pptx + 0430.rtf"
repo_context:
  - "buykings/projects/autopark: collect -> market-radar -> editorial-brief -> Notion -> quality gate -> publish -> retrospective"
status: "codex_handoff_draft"
copyright_note: "책 원문, 방송 전사본, PPT 원문을 재현하지 않고 Autopark 운영 기준과 코드 보강 지시로 재구성한다. 실제 PPT/전사본은 비공개 runtime sample로 다루고, 공개 repo에는 원문 대량 복제를 커밋하지 않는다."
---

# Autopark Editorial Policy v1 — 05. Codex Handoff & Broadcast Asset Runbook

## 0. 한 문장 정의

이 문서는 1~4번 기준서를 실제 Autopark 코드와 프롬프트에 반영하기 위한 **최종 통합 지시서**다.

Autopark의 목표는 단순히 좋은 뉴스 요약을 만드는 것이 아니다.

```text
좋은 Autopark = 오늘 시장의 원인과 방송 첫 꼭지를 판단하고,
그 판단을 뒷받침할 캡처·그래프·표·헤드라인·종목 차트 후보까지
진행자가 바로 PPT로 옮길 수 있는 순서로 제안하는 시스템
```

따라서 Codex 작업의 최종 목적은 다음 네 가지다.

1. `market-radar`가 더 똑똑하게 후보를 점수화한다.
2. `editorial-brief`가 박종훈식 방송 스토리라인과 말할 순서를 만든다.
3. Notion 대시보드가 “읽을 문서”가 아니라 “PPT 제작 큐”가 된다.
4. 방송 후 회고가 실제 방송의 **스토리·순서·장표 사용 여부**를 학습한다.

---

## 1. 이 문서가 해결하려는 문제

현재 Autopark는 이미 다음 뼈대를 갖고 있다.

```text
뉴스/X/시각자료/실적/Finviz/FedWatch 수집
→ market-radar.json
→ editorial-brief.json
→ Notion Markdown
→ 품질검수
→ Notion 발행
→ 방송 후 전사본 회고
```

그러나 실제 방송 샘플을 보면, 최종 산출물은 `3~5개 뉴스 스토리라인`만으로 충분하지 않다. 방송에는 매일 반복되는 시장 지도, 당일 이슈를 보여주는 캡처, 종목별 실적 요약, 5분봉/일봉/주봉 차트, Fed 문구 변화, 금리확률, 헤드라인 카드, 가벼운 이모저모 소재가 함께 필요하다.

즉 Autopark는 이제 다음 단계로 가야 한다.

```text
뉴스 후보 추천기
→ 방송 편집장 + PPT 자료 큐 + 회고 학습기
```

---

## 2. 실제 방송 샘플에서 확인된 구조

### 2.1 2026-04-29 샘플: 실적 과부하 + 하드웨어/AI/오픈AI/시장 주춤

`바이킹 0429.pptx`는 약 35장 규모이며, 앞부분은 시장 기본 지도, 중반은 실적과 교육성 자료, 후반은 OpenAI/트럼프/이란/닷컴버블/게스트 전환으로 구성되어 있다.

관찰된 순서는 다음과 같다.

```text
타이틀/오프닝
→ 주요 지수 흐름
→ S&P500 일봉/주봉
→ Nasdaq/Dow 차트
→ S&P500 히트맵 / Russell2000 히트맵
→ 10년물 국채금리 / WTI / 달러 인덱스 / 원달러 / 비트코인
→ 이번 주 실적발표 기업들
→ 짬 타임: 손익계산서 / 대차대조표 / 잉여현금흐름·EBITDA
→ 테러다인 / 스타벅스 / NXP / 로빈후드 / 시게이트 실적과 차트
→ WSJ OpenAI 매출 목표 미달 이슈와 해석
→ 트럼프·찰스 / 이란·호르무즈 이모저모
→ 닷컴버블과 현재
→ 오늘의 버디버디
```

이 샘플의 핵심은 `실적 시즌`에는 단순 EPS/매출 숫자 나열이 아니라, 진행자가 시청자에게 “실적을 어떻게 봐야 하는지”를 가르치는 교육형 장표가 들어간다는 점이다. 따라서 Autopark는 실적 시즌에 `earnings_education_block` 후보를 만들 수 있어야 한다.

또한 전사본상 진행자는 당일 시장을 “이유를 찾는 시장”, “높아진 기대감”, “AI 인프라 이후 생산성 증명 요구”, “유가·금리·FOMC가 만드는 할인율 부담”으로 설명한다. 이 말은 `market-radar`가 단일 뉴스보다 **국면 해석**을 먼저 만들어야 한다는 뜻이다.

### 2.2 2026-04-30 샘플: FOMC + 빅테크 실적 + 유가/금리 압박

`바이킹 0430.pptx`는 약 45장 규모이며, 실제 방송은 다음 구조에 가깝다.

```text
타이틀/오프닝
→ 시장은 지금 / 4월 FOMC / 빅테크 실적발표 / 일론머스크 화성
→ 주요 지수 흐름
→ S&P500 일봉/주봉 / Nasdaq / 히트맵
→ 10년물 국채금리 / WTI / 원달러
→ 제롬 파월 마지막 FOMC / 인플레이션의 시대
→ 연준 금리 결정 / 문구 변화 / 파월 성명 요약 / 금리인하 횟수 전망
→ 일론머스크 화성 보상 조건
→ 이번 주 실적발표 기업들
→ 빅테크 4인방 실적발표
→ Microsoft / Amazon / Meta / Google 실적 요약과 5분봉·일봉·주봉
→ Qualcomm / OnSemi / Intel 흐름
→ 시장의 싸움: 성장 vs 유가 vs 금리
→ 오늘의 버디버디
```

이 샘플의 핵심은 `Fed day` 또는 `macro shock day`에는 지수와 히트맵보다 **금리·유가·FOMC 문구·금리경로**가 방송 중심축으로 올라올 수 있다는 점이다. 실제 전사본에서도 진행자는 유가와 10년물 금리가 심상치 않기 때문에 일부 차익 실현을 고려할 수 있다고 말하고, 마지막에는 시장이 성장·금리·유가의 삼각 구도에서 싸우고 있다고 정리한다.

### 2.3 두 샘플에서 공통으로 보이는 방송 문법

| 방송 요소 | 실제 역할 | Autopark 변환 |
|---|---|---|
| 오프닝 농담/굿즈/책 이야기 | 사람 냄새와 채널 정체성 | 자동 생성 금지. `host_personalization_slot`으로만 표시 |
| 주요 지수 흐름 | 시장 표면 확인 | `market_snapshot` 필수 카드 |
| S&P/Nasdaq/히트맵 | 오늘 시장의 한 장면 | `visual_anchor` 우선 후보 |
| 10년물/유가/달러/원달러 | 할인율·리스크 프리미엄·한국장 연결 | `macro_risk_spine` |
| 경제 일정/실적 일정 | 오늘 왜 바쁜지 설명 | `calendar_context` |
| 실적 요약 슬라이드 | 숫자를 방송 언어로 압축 | `earnings_card` |
| 5분봉/일봉/주봉 | 시장 반응과 위치감 | `stock_chart_pack` |
| FOMC 문구 변화 | 정책 변화의 시각적 증거 | `statement_diff_card` |
| X/이모저모/밈 | 분위기·재미·전환 | `light_segment`, 사실 근거로 승격 금지 |
| 게스트 전환 | 시간 제약과 진행 흐름 | `guest_cutoff_mode` 반영 |

---

## 3. 1~4번 기준서의 코드 반영 위치

| 기준서 | 핵심 내용 | 반영 대상 |
|---|---|---|
| 01 Morning Routine | 오늘 시장 원인, 핵심 질문, 한두 줄 관점, 말할 순서 | `build_editorial_brief.py`, `build_live_notion_dashboard.py` |
| 02 Signal/Noise | 첫 꼭지, 시그널/노이즈, 기대 대비 결과, 선반영 | `build_market_radar.py`, `build_editorial_brief.py`, quality gate |
| 03 Source Roles | Reuters/CNBC/Bloomberg/X/Finviz 등 소스 역할 | `source registry`, `evidence_to_use`, `evidence_to_drop` |
| 04 Market Map | 지수·히트맵·섹터·주도주·고정 체크리스트 | `visual-cards.json`, Datawrapper, Notion 시장 카드 |
| 05 Integration | 코드/프롬프트/자료 큐/회고 결합 | 전체 파이프라인 |

---

## 4. Codex 작업의 최우선 원칙

### 4.1 Notion은 “최종 보고서”가 아니라 “PPT 제작 큐”여야 한다

실제 방송은 PPT를 보며 진행된다. 따라서 Notion 대시보드에는 단순 문장 요약보다 다음 정보가 더 중요하다.

```text
이 소재를 몇 번째 꼭지로 쓸지
어떤 장표가 필요한지
그 장표는 캡처인지, Datawrapper 그래프인지, 내부 표인지
말로만 처리해도 되는지
자료가 없으면 어떤 fallback으로 처리할지
```

### 4.2 모든 스토리라인은 `talk`와 `slide`를 분리해야 한다

각 후보는 다음 중 하나로 분류한다.

| 유형 | 의미 |
|---|---|
| `slide_required` | 차트/표/캡처가 없으면 설명력이 떨어짐 |
| `slide_recommended` | 장표가 있으면 좋지만 말로도 가능 |
| `talk_only` | 말로 처리하는 편이 낫고 장표화하면 속도가 느려짐 |
| `light_segment` | 방송감·재미용. 사실 판단의 핵심 근거가 아님 |
| `drop` | 오늘 방송에는 쓰지 않음 |

### 4.3 사람 냄새는 슬롯으로 남기되, 모델이 흉내 내지 않는다

0429/0430 방송에는 오프닝 농담, 책 리뷰, 티셔츠, 개인적인 “냄새” 표현, 게스트 전환 멘트가 있다. 이것은 진행자의 강점이지만 모델이 그대로 생성하면 부자연스럽거나 위험하다.

따라서 Autopark는 다음 원칙을 따른다.

```text
모델은 개인 농담을 생성하지 않는다.
모델은 “여기서 진행자가 개인화할 수 있는 가벼운 오프닝 슬롯”만 표시한다.
방송용 문장은 사실·해석·자료 연결 중심으로 쓴다.
```

### 4.4 방송 모드가 있어야 한다

실제 방송은 매일 같은 길이와 구조로 가지 않는다. 0429는 실적이 너무 많아 진행자가 자료 준비 부담을 직접 언급했고, 0430은 FOMC와 빅테크 실적이 겹친 날이었다. 따라서 Autopark는 매일 `broadcast_mode`를 먼저 판정해야 한다.

권장 모드:

```yaml
broadcast_mode:
  normal: "일반 시장 브리핑"
  earnings_heavy: "실적 발표 기업이 많아 종목 카드와 실적 교육 블록 우선"
  fed_day: "FOMC/연준/금리경로가 중심"
  macro_shock: "유가·금리·달러·지정학 등 매크로 충격이 중심"
  guest_early: "게스트가 일찍 들어와 진행자 단독 시간이 짧음"
  no_guest_long_host: "진행자 단독 시간이 길어 심층 설명 가능"
  holiday_korea_market_open: "한국은 휴일이지만 미국장/방송은 진행되는 특수 모드"
```

---

## 5. 새로 추가할 파일/설정 제안

### 5.1 정책 문서 위치

권장 경로:

```text
projects/autopark/docs/editorial-policy/
  01-morning-routine.md
  02-signal-noise-lead-selection.md
  03-source-roles.md
  04-market-map-checklist.md
  05-codex-handoff-runbook.md
```

이 5개 문서는 프롬프트 원문으로 매번 전부 주입하기보다, 코드가 요약된 정책 YAML을 읽고, 상세 문서는 사람이 검토할 때 참고하는 구조가 좋다.

### 5.2 정책 매니페스트

새 파일:

```text
projects/autopark/config/editorial_policy_manifest.yml
```

예시:

```yaml
version: "2026-05-02"
policy_docs:
  morning_routine: "projects/autopark/docs/editorial-policy/01-morning-routine.md"
  signal_noise: "projects/autopark/docs/editorial-policy/02-signal-noise-lead-selection.md"
  source_roles: "projects/autopark/docs/editorial-policy/03-source-roles.md"
  market_map: "projects/autopark/docs/editorial-policy/04-market-map-checklist.md"
  integration: "projects/autopark/docs/editorial-policy/05-codex-handoff-runbook.md"

active_rules:
  require_source_roles: true
  require_signal_noise_label: true
  require_talk_vs_slide: true
  require_visual_asset_queue: true
  require_retrospective_feedback: true
  forbid_x_reddit_as_fact_anchor: true
  forbid_internal_scoring_exposure: true
```

### 5.3 방송 모드 설정

새 파일:

```text
projects/autopark/config/broadcast_modes.yml
```

예시:

```yaml
modes:
  normal:
    min_storylines: 3
    max_storylines: 5
    fixed_market_assets: "standard"
    earnings_cards: "selective"
    max_dynamic_assets: 8

  earnings_heavy:
    min_storylines: 3
    max_storylines: 4
    fixed_market_assets: "compressed"
    earnings_cards: "expanded"
    allow_earnings_education_block: true
    max_dynamic_assets: 14

  fed_day:
    min_storylines: 3
    max_storylines: 5
    fixed_market_assets: "standard"
    require_fed_statement_diff: true
    require_rate_path_asset: true
    max_dynamic_assets: 10

  macro_shock:
    min_storylines: 2
    max_storylines: 4
    fixed_market_assets: "macro_first"
    require_macro_spine: true
    max_dynamic_assets: 8

  guest_early:
    min_storylines: 2
    max_storylines: 3
    fixed_market_assets: "compressed"
    max_dynamic_assets: 6
```

### 5.4 시각 자료 매니페스트

새 파일:

```text
projects/autopark/config/visual_asset_manifest.yml
```

핵심은 `무엇을 캡처할지`보다 `왜 필요한지`를 적는 것이다.

```yaml
assets:
  major_indices_table:
    section: "market_now"
    type: "data_table"
    role: ["market_snapshot"]
    default_priority: "required"
    render_method: "internal_table_or_datawrapper"
    fallback: "text_summary"

  sp500_daily_chart:
    section: "market_now"
    type: "chart"
    role: ["index_context", "visual_anchor"]
    default_priority: "required"
    render_method: "datawrapper_or_yfinance_chart"
    fallback: "major_indices_table"

  sp500_weekly_chart:
    section: "market_now"
    type: "chart"
    role: ["trend_context"]
    default_priority: "recommended"
    render_method: "datawrapper_or_yfinance_chart"

  sp500_heatmap:
    section: "market_now"
    type: "screenshot"
    role: ["market_breadth", "sector_rotation", "visual_anchor"]
    default_priority: "required"
    source_id: "finviz-sp500-heatmap"
    render_method: "playwright_capture"

  russell2000_heatmap:
    section: "market_now"
    type: "screenshot"
    role: ["smallcap_breadth"]
    default_priority: "conditional"
    condition: "small_caps_move_or_risk_appetite_story"

  us10y_chart:
    section: "macro_risk"
    type: "chart"
    role: ["rates_signal", "discount_rate"]
    default_priority: "conditional_required"
    condition: "rates_move_or_fed_day_or_growth_pressure"

  wti_chart:
    section: "macro_risk"
    type: "chart"
    role: ["oil_inflation", "geopolitical_risk"]
    default_priority: "conditional_required"
    condition: "oil_move_or_middle_east_or_inflation_story"

  usdkrw_chart:
    section: "korea_relevance"
    type: "chart"
    role: ["korea_market_link"]
    default_priority: "conditional"
    condition: "dollar_or_korea_open_relevance"

  earnings_calendar:
    section: "calendar"
    type: "table"
    role: ["why_today_is_busy"]
    default_priority: "conditional_required"
    condition: "earnings_heavy_or_bigtech_reporting"

  fed_statement_diff:
    section: "fed_day"
    type: "text_diff_card"
    role: ["policy_signal", "wording_change"]
    default_priority: "conditional_required"
    condition: "fed_day"

  fedwatch_rate_path:
    section: "fed_day"
    type: "datawrapper_table"
    role: ["rate_path", "market_expectation"]
    default_priority: "conditional_required"
    condition: "fed_day_or_rates_signal"

  stock_5min_chart:
    section: "earnings"
    type: "chart"
    role: ["immediate_market_reaction"]
    default_priority: "conditional"
    condition: "after_hours_or_earnings_reaction"

  stock_daily_chart:
    section: "earnings"
    type: "chart"
    role: ["short_term_positioning"]
    default_priority: "conditional"

  stock_weekly_chart:
    section: "earnings"
    type: "chart"
    role: ["trend_positioning"]
    default_priority: "conditional"
```

### 5.5 소스 역할 설정

3번 기준서의 내용을 코드가 읽을 수 있게 다음 파일로 둔다.

```text
projects/autopark/config/source_roles.yml
```

이 파일은 이미 작성한 3번 기준서의 YAML 초안을 정리해 넣으면 된다. 핵심 필드는 다음과 같다.

```yaml
source_id:
  source_type: "legacy_media | data_platform | official | x | reddit | visual_site"
  evidence_roles: ["fact_anchor", "data_anchor", "interpretation", "sentiment_probe", "visual_anchor"]
  broadcast_roles: ["hook", "market_reaction", "deep_context", "light_segment", "ppt_asset"]
  cannot_be_used_for: ["fact_anchor"]
  required_pairing: ["Reuters", "Bloomberg", "official filing"]
  reliability_notes: "짧은 운영 메모"
```

---

## 6. `market-radar.json` 보강 지시

### 6.1 현재 역할

`market-radar`는 수집 후보를 방송용 후보 장부로 점수화하는 단계다. 지금까지는 중요도와 후보 묶음에 초점이 있었다면, 앞으로는 다음 세 가지를 반드시 추가해야 한다.

```text
1. 이 후보가 어떤 방송 단계에 쓰이는가?
2. 이 후보는 말로 처리할 것인가, 장표가 필요한가?
3. 이 후보를 뒷받침할 소스와 시각 자료가 충분한가?
```

### 6.2 후보 객체 확장 스키마

```json
{
  "item_id": "news_20260430_001",
  "topic_cluster_id": "fed_policy_20260430",
  "title": "FOMC statement wording turned more inflation-wary",
  "summary_ko": "연준이 인플레이션 표현을 더 강하게 바꾸고 금리 동결 반대표가 늘었다.",
  "source_ids": ["reuters_001", "fed_statement", "cme_fedwatch"],
  "source_roles": ["fact_anchor", "official", "data_anchor"],
  "signal_axes": ["rates_signal", "macro_signal", "policy_signal"],
  "signal_or_noise": "signal",
  "expectation_gap": {
    "level": "high",
    "reason": "금리 동결은 예상됐지만 반대표와 문구 변화가 정책 경로 해석을 바꿈"
  },
  "market_reaction": {
    "assets_checked": ["us10y", "nasdaq", "russell2000", "wti", "usdkrw"],
    "reaction_summary": "금리·유가 부담이 성장주 기대를 눌렀는지 확인 필요"
  },
  "broadcast_stage": "macro_policy",
  "lead_score_components": {
    "market_causality": 18,
    "structural_signal": 18,
    "expectation_gap": 14,
    "breadth_and_contagion": 10,
    "evidence_quality": 14,
    "broadcast_fit": 10,
    "timing_urgency": 8
  },
  "lead_score_100": 92,
  "talk_vs_slide": "slide_required",
  "asset_needs": ["fed_statement_diff", "fedwatch_rate_path", "us10y_chart"],
  "korea_open_relevance": "high",
  "drop_reason": null
}
```

### 6.3 후보의 `broadcast_stage` 표준값

```yaml
broadcast_stage:
  - opening_question
  - market_now
  - macro_policy
  - earnings_calendar
  - earnings_deep_dive
  - sector_rotation
  - feature_stock
  - sentiment_check
  - light_segment
  - guest_transition
  - drop
```

### 6.4 0429/0430 샘플에서 뽑은 특수 모드

```yaml
earnings_education_block:
  when:
    - earnings_heavy == true
    - multiple_stocks_require_accounting_explanation == true
  examples:
    - 손익계산서
    - 대차대조표
    - 잉여현금흐름 / EBITDA
  output:
    - educational_slide_candidates
    - short_explainer_talk_track

risk_triangle:
  when:
    - growth_story_is_strong == true
    - rates_or_oil_pressure == true
  axes:
    - growth
    - rates
    - oil
  output:
    - market_frame_card
    - closing_synthesis
```

---

## 7. `editorial-brief.json` 보강 지시

### 7.1 현재 필드 유지

기존 필드인 `daily_thesis`, `editorial_summary`, `storylines`, `recommendation_stars`, `hook`, `why_now`, `core_argument`, `talk_track`, `counterpoint`, `evidence_to_use`, `evidence_to_drop`은 유지한다.

### 7.2 추가할 최상위 필드

```json
{
  "date": "YYYY-MM-DD",
  "broadcast_mode": "fed_day",
  "daily_thesis": "강한 빅테크 실적에도 유가와 금리 부담이 시장의 기대수익률을 압박한다.",
  "one_line_market_frame": "오늘 시장의 싸움은 성장, 유가, 금리의 삼각 구도다.",
  "opening_question": "실적은 좋은데 왜 시장은 마음껏 못 오르는가?",
  "market_now": {...},
  "broadcast_rundown": [...],
  "storylines": [...],
  "ppt_asset_queue": [...],
  "talk_only_queue": [...],
  "drop_list": [...],
  "retrospective_watchpoints": [...]
}
```

### 7.3 `broadcast_rundown` 스키마

`broadcast_rundown`은 Notion 상단에 바로 노출될 수 있어야 한다.

```json
{
  "order": 1,
  "stage": "market_now",
  "title": "주요 지수와 시장 분위기",
  "duration_hint": "3-5분",
  "why_here": "개별 뉴스 전에 시장 표면과 리스크 압력을 먼저 보여준다.",
  "slides_needed": ["major_indices_table", "sp500_daily_chart", "sp500_heatmap", "us10y_chart", "wti_chart"],
  "talk_track": "지수는 크게 무너지지 않았지만 10년물과 유가가 할인율 부담을 키우는지 확인한다.",
  "transition_to_next": "이 압박이 FOMC 문구 변화와 어떻게 연결되는지 본다."
}
```

### 7.4 `ppt_asset_queue` 스키마

```json
{
  "asset_id": "us10y_chart_20260430",
  "asset_type": "chart",
  "asset_role": ["rates_signal", "macro_risk_spine"],
  "broadcast_stage": "market_now",
  "priority": "required",
  "source_id": "market_charts.us10y",
  "render_method": "datawrapper_png",
  "capture_status": "ready | failed | missing | fallback_used",
  "paired_storyline_ids": ["story_fed_policy_001"],
  "why_needed": "금리 부담이 성장주 반응을 누르는지 설명하는 핵심 그림이다.",
  "talk_vs_slide": "slide_required",
  "fallback": {
    "type": "text_summary",
    "text": "10년물 금리 방향만 표로 표시"
  },
  "notion_render_hint": "PPT 후보 자료 / 시장은 지금"
}
```

### 7.5 스토리라인 객체 보강

```json
{
  "storyline_id": "story_google_earnings_001",
  "rank": 2,
  "recommendation_stars": 3,
  "lead_candidate": false,
  "title": "구글 실적은 AI 시대의 수익성 증명에 가장 가까웠다",
  "hook": "AI 경쟁자가 많아도 구글 검색과 클라우드는 숫자로 버텼다.",
  "why_now": "빅테크 실적이 동시에 나온 날, 시장은 AI 투자가 비용인지 생산성인지 따진다.",
  "core_argument": "클라우드 성장과 EPS 서프라이즈가 높아진 AI 기대를 일부 정당화한다.",
  "signal_or_noise": "signal",
  "signal_axes": ["earnings_signal", "industry_structure_signal"],
  "expectation_gap": "positive_surprise_but_high_expectation",
  "prepricing_risk": "medium",
  "talk_vs_slide": "slide_required",
  "visual_strategy": {
    "primary": "earnings_card",
    "secondary": ["stock_5min_chart", "stock_daily_chart"],
    "talk_only_parts": ["검색 경쟁자에 대한 해석"]
  },
  "evidence_to_use": [
    {"item_id": "earnings_google_001", "role": "numbers"},
    {"item_id": "stockchart_google_5min", "role": "market_reaction"}
  ],
  "evidence_to_drop": [
    {"item_id": "x_hot_take_123", "drop_code": "sentiment_only"}
  ],
  "counterpoint": "CAPEX 증가와 유튜브 광고 부진은 비용·성장률 부담으로 남는다.",
  "first_5min_fit": "medium",
  "korea_open_relevance": "medium"
}
```

---

## 8. `build_editorial_brief.py` 프롬프트 보강안

### 8.1 시스템 프롬프트 핵심 블록

아래 블록을 기존 편집장 프롬프트에 병합한다.

```text
You are the editorial producer for a 7:20 KST morning market broadcast.
Your job is not to summarize all collected news.
Your job is to decide what the host should say first, what should be shown as PPT material,
what can be handled verbally, and what should be dropped.

Follow these principles:
1. Start from the question: what actually moved the market today?
2. Separate signal from noise.
3. Separate fact evidence, data evidence, interpretation, sentiment, and visual material.
4. Never use X/Reddit/social-only material as a fact anchor.
5. Every top storyline must declare whether it is slide_required, slide_recommended, talk_only, or drop.
6. Every slide_required storyline must produce a PPT asset queue.
7. Do not imitate the host's personal jokes or private style. Only mark optional host_personalization_slot.
8. If the day is earnings-heavy, compress the fixed market section and prioritize earnings cards.
9. If the day is a Fed/macro day, prioritize rate path, statement wording, 10Y, WTI, DXY/USDKRW, and market reaction.
10. If a guest segment starts early, output a shorter rundown with fewer dynamic assets.
```

### 8.2 출력 지시 블록

```text
Return valid JSON only.
The JSON must include:
- broadcast_mode
- daily_thesis
- one_line_market_frame
- opening_question
- market_now
- broadcast_rundown[]
- storylines[]
- ppt_asset_queue[]
- talk_only_queue[]
- drop_list[]
- retrospective_watchpoints[]

For each storyline, include:
- rank
- recommendation_stars
- lead_candidate
- signal_or_noise
- signal_axes
- expectation_gap
- talk_vs_slide
- visual_strategy
- evidence_to_use with item_id
- evidence_to_drop with drop_code
- first_5min_fit
- korea_open_relevance

For each asset in ppt_asset_queue, include:
- asset_id
- asset_type
- asset_role
- broadcast_stage
- priority
- source_id
- render_method
- paired_storyline_ids
- why_needed
- fallback
```

### 8.3 금지 문장

모델이 사용자 노출 문장에 쓰지 말아야 할 것:

```text
- 내부 점수는 87점입니다.
- 클러스터 개수가 많아서 중요합니다.
- LLM이 판단하기에...
- X에서 많이 돌기 때문에 사실입니다.
- 정확한 출처는 없지만...
- 진행자가 이런 농담을 하면 좋습니다.
```

대신 사용 가능한 표현:

```text
- 여러 주요 출처에서 반복되고, 시장 가격 반응도 동반되어 핵심 후보입니다.
- 숫자는 좋지만 기대가 이미 높아 가이던스가 중요합니다.
- 이 자료는 사실 근거가 아니라 시장 심리 확인용입니다.
- 이 이슈는 장표보다 말로 짧게 처리하는 편이 좋습니다.
```

---

## 9. Notion 대시보드 구조 보강

### 9.1 기존 상단 구조 유지 + PPT 큐 추가

기존 구조:

```text
오늘의 핵심 질문
→ 추천 스토리라인
→ 자료 수집
```

권장 구조:

```text
오늘의 핵심 질문
→ 오늘의 방송 모드
→ 3분 시장 지도
→ 추천 방송 순서
→ PPT 후보 자료 큐
→ 추천 스토리라인 상세
→ 말로만 처리할 자료
→ 버릴 자료와 이유
→ 원자료 수집 목록
```

### 9.2 Notion 상단 예시

```markdown
# 26.04.30 Autopark Morning Brief

## 오늘의 핵심 질문
실적은 좋은데 왜 시장은 마음껏 오르지 못하는가?

## 방송 모드
`fed_day + earnings_heavy + macro_risk`

## 오늘의 한 줄
강한 빅테크 실적에도 유가와 10년물 금리 부담이 기대수익률을 누르며, 시장은 성장·금리·유가의 삼각 구도에서 싸우고 있다.

## 3분 시장 지도
- 지수: S&P/Nasdaq은 제한적 하락, Russell은 약세
- 리스크: WTI 급등, 10년물 금리 부담
- 히트맵: 빅테크와 반도체 온도 차이 확인
- 한국장 연결: 원달러/유가/반도체 수급 확인

## 추천 방송 순서
1. 시장은 지금: 지수보다 유가와 10년물 금리를 먼저 보자
2. 4월 FOMC: 금리 동결은 예상, 문구와 반대표가 메시지
3. 빅테크 실적: 숫자는 좋지만 비용·CAPEX·기대치가 관건
4. 개별 종목: 구글/메타/MS/아마존/퀄컴 반응 비교
5. 마무리: 성장 vs 금리 vs 유가

## PPT 후보 자료 큐
| 우선순위 | 자료 | 역할 | 생성 방식 | 연결 꼭지 |
|---|---|---|---|---|
| required | 주요 지수 흐름 | 시장 표면 | Datawrapper/table | 시장은 지금 |
| required | 10년물 국채금리 | 할인율 부담 | Datawrapper PNG | 시장은 지금/FOMC |
| required | WTI | 인플레·지정학 부담 | Datawrapper PNG | 시장은 지금/FOMC |
| required | FOMC 문구 변화 | 정책 신호 | text diff card | 4월 FOMC |
| required | FedWatch 금리경로 | 기대 변화 | Datawrapper table | 4월 FOMC |
| required | 빅테크 실적 요약표 | 실적 비교 | internal table | 빅테크 실적 |
```

---

## 10. 품질 게이트 보강

`review_dashboard_quality.py`에 아래 검사를 추가한다.

### 10.1 통합 품질 게이트 코드

```yaml
INT-001:
  name: "broadcast_mode_exists"
  rule: "editorial_brief.broadcast_mode is present and one of allowed modes"
  severity: "error"

INT-002:
  name: "daily_thesis_has_causal_structure"
  rule: "daily_thesis includes cause + market reaction + broadcast angle"
  severity: "warning"

INT-003:
  name: "storylines_have_talk_vs_slide"
  rule: "every storyline has talk_vs_slide"
  severity: "error"

INT-004:
  name: "slide_required_has_asset"
  rule: "every slide_required storyline has at least one ppt_asset_queue item"
  severity: "error"

INT-005:
  name: "x_reddit_not_fact_anchor"
  rule: "items with source_type in [x, reddit] cannot be sole fact_anchor unless direct_source"
  severity: "error"

INT-006:
  name: "earnings_story_has_required_numbers"
  rule: "earnings story includes revenue/EPS/guidance or explicit missing_reason"
  severity: "warning"

INT-007:
  name: "fed_story_has_policy_assets"
  rule: "fed_day requires statement_diff or rate_path asset"
  severity: "error"

INT-008:
  name: "market_map_has_fixed_spine"
  rule: "normal/fed_day/macro_shock modes include market snapshot + at least one index chart/heatmap + macro risk chart"
  severity: "warning"

INT-009:
  name: "no_host_joke_imitation"
  rule: "dashboard text does not invent personal jokes or host self-referential banter"
  severity: "warning"

INT-010:
  name: "no_internal_logic_exposure"
  rule: "no visible text exposes score, cluster count, prompt, internal ID except source labels"
  severity: "error"

INT-011:
  name: "drop_list_has_reasons"
  rule: "drop_list items include drop_code"
  severity: "warning"

INT-012:
  name: "asset_queue_not_overloaded"
  rule: "dynamic asset count respects broadcast_mode.max_dynamic_assets unless override_reason exists"
  severity: "warning"

INT-013:
  name: "korea_relevance_checked"
  rule: "top storylines include korea_open_relevance"
  severity: "warning"

INT-014:
  name: "fallback_asset_present"
  rule: "capture-dependent required assets include fallback"
  severity: "warning"
```

### 10.2 실적 카드 품질 기준

실적 스토리라인은 아래 중 최소 5개를 가져야 한다.

```text
- 매출 성장률 또는 매출 컨센서스 대비 결과
- EPS 성장률 또는 EPS 컨센서스 대비 결과
- 영업이익/마진/매출총이익률 중 하나
- 가이던스
- 주가 반응: 5분봉/애프터/일봉/주봉 중 하나
- 기대치 수준: 낮음/보통/높음/극단
- CAPEX/현금흐름/부채/수주잔고 중 해당 항목
- 본업과 부업/아픈 손가락 구분
- 시장이 좋아한 이유와 싫어한 이유
```

### 10.3 FOMC/연준 카드 품질 기준

Fed day 스토리라인은 아래 중 최소 5개를 가져야 한다.

```text
- 금리 결정 결과
- 예상과 실제의 차이
- 반대표/위원 구성/점도표/성명 문구 변화 중 하나
- 파월 발언 또는 성명 요약
- FedWatch/금리인하 확률 변화
- 10년물 금리 반응
- 달러/주식/섹터/러셀 반응
- 인플레이션/고용/유가와 연결
- 시장이 앞으로 볼 다음 이벤트
```

---

## 11. 방송 후 회고 runbook 결합

### 11.1 현재 회고의 한계

현재 회고는 전사본과 대시보드를 비교하는 데 초점이 있다. 그러나 실제 방송은 PPT 장표와 전사본이 함께 있어야 제대로 평가된다.

전사본만 보면 “말한 주제”는 알 수 있지만, 다음은 알기 어렵다.

```text
어떤 장표가 실제로 쓰였는가?
어떤 장표는 만들었지만 건너뛰었는가?
어떤 내용은 장표 없이 말로만 처리했는가?
진행자가 순서를 바꾼 이유가 시간 때문인지, 자료 품질 때문인지, 방송감 때문인지?
```

따라서 회고는 `transcript-only`에서 `transcript + PPT outline + dashboard` 비교로 확장해야 한다.

### 11.2 추가 스크립트 제안

```text
projects/autopark/scripts/extract_ppt_outline.py
projects/autopark/scripts/build_actual_broadcast_outline.py
projects/autopark/scripts/compare_dashboard_to_broadcast_assets.py
```

#### `extract_ppt_outline.py`

입력:

```text
runtime/samples/YYYY-MM-DD/broadcast.pptx
```

출력:

```text
runtime/broadcast/YYYY-MM-DD/ppt-outline.json
runtime/broadcast/YYYY-MM-DD/ppt-outline.md
```

출력 예시:

```json
{
  "date": "2026-04-30",
  "slide_count": 45,
  "slides": [
    {"slide_no": 3, "title": "시장은 지금 / 4월 FOMC / 빅테크 실적발표", "detected_stage": "opening_question"},
    {"slide_no": 10, "title": "10년물 국채금리", "detected_stage": "macro_risk"},
    {"slide_no": 15, "title": "연준 금리 결정", "detected_stage": "macro_policy"},
    {"slide_no": 24, "title": "마이크로소프트 1분기 실적발표", "detected_stage": "earnings_deep_dive"}
  ]
}
```

#### `build_actual_broadcast_outline.py`

입력:

```text
host-segment.md
ppt-outline.json
```

출력:

```text
runtime/broadcast/YYYY-MM-DD/actual-broadcast-outline.json
```

역할:

```text
전사본에서 실제 말한 주제와 PPT slide title을 매칭한다.
말로만 처리한 주제와 장표로 처리한 주제를 나눈다.
게스트 전환 시점을 기록한다.
```

#### `compare_dashboard_to_broadcast_assets.py`

입력:

```text
runtime/notion/YYYY-MM-DD/YY.MM.DD.md
editorial-brief.json
market-radar.json
actual-broadcast-outline.json
ppt-outline.json
```

출력:

```text
runtime/reviews/YYYY-MM-DD/broadcast-asset-retrospective.json
runtime/reviews/YYYY-MM-DD/broadcast-asset-retrospective.md
```

비교 항목:

```text
- 추천 스토리라인이 실제 방송에 쓰였는가?
- 추천한 장표가 실제 PPT에 있었는가?
- 실제 PPT에 있었지만 Autopark가 놓친 장표는 무엇인가?
- Autopark가 추천했지만 실제 방송에서 쓰이지 않은 자료는 무엇인가?
- 실제 방송에서는 말로 처리했는데 Autopark가 장표를 요구한 자료는 무엇인가?
- 실제 방송에서는 장표가 필요했는데 Autopark가 말로만 처리하라고 한 자료는 무엇인가?
```

### 11.3 회고 라벨 확장

```yaml
storyline_labels:
  used_as_lead: "첫 꼭지로 사용됨"
  used_later: "후반부 꼭지로 사용됨"
  merged_into_market_frame: "시장 총평 안에 흡수됨"
  mentioned_only: "장표 없이 말로만 언급됨"
  not_used_time_cut: "시간 부족으로 제외"
  not_used_guest_cutoff: "게스트 전환 때문에 제외"
  not_used_low_visual_value: "보여줄 그림이 약해 제외"
  not_used_too_complex: "방송에서 풀기 복잡해 제외"
  not_used_already_known: "새 정보가 아니라 제외"
  false_positive_sentiment_only: "심리 과열을 실제 시그널로 오판"

asset_labels:
  asset_used: "실제 PPT/방송에서 사용됨"
  asset_created_not_used: "만들었지만 방송에서 사용되지 않음"
  asset_missing_needed: "필요했지만 Autopark가 만들지 못함"
  asset_talk_only_better: "장표보다 말로 처리하는 편이 나았음"
  asset_overproduced: "자료가 과하게 많았음"
  asset_capture_failed: "캡처 실패로 누락됨"
  asset_fallback_used: "대체 자료로 처리됨"

sequence_labels:
  sequence_match: "추천 순서와 실제 방송 순서가 대체로 일치"
  sequence_partial: "핵심 소재는 맞았지만 순서가 다름"
  sequence_miss: "실제 방송 흐름과 다름"
  mode_miss: "broadcast_mode 판정 실패"
```

### 11.4 0429/0430을 회고 테스트로 쓰는 법

```yaml
sample_0429:
  expected_mode:
    - earnings_heavy
    - market_pause_after_rally
    - ai_hardware_rotation
  must_detect:
    - fixed_market_spine
    - earnings_education_block
    - multiple_earnings_cards
    - OpenAI_issue_as_noise_or_single_company_issue_not_whole_hardware_collapse
    - macro_risk_from_oil_rates_fomc
  retrospective_questions:
    - "실적 카드가 단순 숫자 나열을 넘어 기대치/가이던스/주가 반응을 설명했는가?"
    - "OpenAI 이슈를 AI 하드웨어 전체 약세로 과잉 일반화하지 않았는가?"
    - "교육형 장표를 제안했는가?"

sample_0430:
  expected_mode:
    - fed_day
    - earnings_heavy
    - macro_risk
  must_detect:
    - fixed_market_spine
    - FOMC_statement_diff
    - rate_path_expectation
    - bigtech_earnings_cards
    - risk_triangle_growth_rates_oil
  retrospective_questions:
    - "유가와 10년물 금리를 시장 압박의 중심축으로 올렸는가?"
    - "FOMC는 금리 결정 결과보다 문구 변화와 반대표를 더 중요하게 다뤘는가?"
    - "빅테크 실적을 단순 좋음/나쁨이 아니라 기대치와 비용 부담으로 나눴는가?"
```

---

## 12. 자료 수집/캡처 시스템 보강

### 12.1 캡처는 “내부 증빙”과 “PPT 후보”를 구분한다

모든 캡처가 PPT에 들어가는 것은 아니다. 캡처의 목적을 나눠야 한다.

| 캡처 목적 | 설명 | 노출 여부 |
|---|---|---|
| `internal_evidence` | 모델 판단과 사람 검토용 증빙 | Notion 하단 또는 runtime만 |
| `ppt_candidate` | 진행자가 PPT에 바로 쓸 수 있는 자료 | Notion 상단 큐에 노출 |
| `site_diagnostic` | 사이트 로딩/로그인/Cloudflare 문제 확인 | 내부 로그만 |
| `fallback_material` | 주요 캡처 실패 시 대체 자료 | 조건부 노출 |

### 12.2 고정 캡처/그래프 우선순위

방송 샘플상 매일 반복될 가능성이 높은 우선순위는 다음과 같다.

```yaml
required_or_near_required:
  - 주요 지수 흐름
  - S&P500 일봉
  - S&P500 주봉
  - Nasdaq 일봉
  - S&P500 히트맵
  - Russell2000 히트맵
  - 10년물 국채금리
  - WTI
  - 원달러

conditional:
  - 달러 인덱스
  - 비트코인
  - FedWatch 단기/장기 금리확률
  - 경제 일정
  - 실적발표 캘린더
  - 개별 종목 5분봉/일봉/주봉
  - FOMC 문구 변화 카드
  - 공식 성명/실적 발표 요약 카드
  - X/Reddit/밈 캡처
```

### 12.3 동적 자료 생성 규칙

#### 실적 카드

실적 카드는 다음 템플릿을 따른다.

```text
[기업명] [분기] 실적
- 핵심 숫자: 매출/EPS/영업이익/마진
- 시장 기대 대비: 상회/하회/혼재
- 좋았던 점: 본업/클라우드/광고/수주/현금흐름 등
- 아쉬운 점: 가이던스/CAPEX/부문 부진/중국/비용
- 주가 반응: 5분봉/애프터/일봉
- 해석: 기대치가 낮았나, 높았나, 숫자가 기대를 바꿨나
```

#### FOMC 카드

```text
[이벤트명]
- 결정: 동결/인상/인하
- 예상과 차이: 예상 부합/서프라이즈
- 문구 변화: 이전 표현 → 새 표현
- 반대표/위원 메시지
- 파월/성명 핵심 문장 요약
- 시장 반응: 10년물, 달러, 성장주, 러셀
- 다음 확인 포인트: 다음 지표/다음 회의/점도표
```

#### 시장의 싸움 카드

0430 샘플처럼 여러 힘이 충돌할 때는 `market_tension_card`를 만든다.

```json
{
  "asset_id": "market_tension_growth_rates_oil",
  "asset_type": "concept_card",
  "title": "시장의 싸움",
  "axes": ["성장", "금리", "유가"],
  "use_when": "강한 실적과 높은 할인율/유가가 동시에 존재할 때",
  "talk_track": "성장이 리스크 프리미엄을 압도하는 기업만 살아남는 국면인지 확인한다."
}
```

---

## 13. 코드 작업 순서

### Phase 0 — 문서와 샘플 정리

1. 1~5번 정책 문서를 `projects/autopark/docs/editorial-policy/`에 넣는다.
2. 실제 방송 PPT/전사본은 공개 repo에 원문으로 커밋하지 않는다.
3. 샘플은 로컬 또는 git-ignored runtime 경로에 둔다.

권장 경로:

```text
projects/autopark/runtime/samples/2026-04-29/broadcast.pptx
projects/autopark/runtime/samples/2026-04-29/transcript.rtf
projects/autopark/runtime/samples/2026-04-30/broadcast.pptx
projects/autopark/runtime/samples/2026-04-30/transcript.rtf
```

### Phase 1 — 스키마 확장

수정 대상:

```text
projects/autopark/scripts/build_market_radar.py
projects/autopark/scripts/build_editorial_brief.py
projects/autopark/scripts/build_live_notion_dashboard.py
projects/autopark/scripts/review_dashboard_quality.py
```

작업:

```text
- broadcast_mode 추가
- talk_vs_slide 추가
- ppt_asset_queue 추가
- signal_axes 추가
- expectation_gap/prepricing_risk 추가
- evidence_role/source_role 추가
- drop_code 추가
```

### Phase 2 — 설정 파일 추가

추가:

```text
projects/autopark/config/editorial_policy_manifest.yml
projects/autopark/config/broadcast_modes.yml
projects/autopark/config/visual_asset_manifest.yml
projects/autopark/config/source_roles.yml
```

### Phase 3 — 편집장 프롬프트 업데이트

수정 대상:

```text
projects/autopark/scripts/build_editorial_brief.py
```

작업:

```text
- 1~4번 기준서 요약 규칙을 프롬프트에 반영
- 실제 방송 샘플에서 도출한 broadcast_mode/talk_vs_slide/asset_queue 규칙 반영
- JSON schema 검증 강화
- fallback brief에도 최소한 broadcast_mode와 ppt_asset_queue placeholder를 넣기
```

### Phase 4 — Notion 렌더링 업데이트

수정 대상:

```text
projects/autopark/scripts/build_live_notion_dashboard.py
```

작업:

```text
- 상단에 방송 모드와 오늘의 한 줄 추가
- 3분 시장 지도 카드 추가
- 추천 방송 순서 추가
- PPT 후보 자료 큐 추가
- 말로만 처리할 자료와 버릴 자료 분리
```

### Phase 5 — 품질 게이트 업데이트

수정 대상:

```text
projects/autopark/scripts/review_dashboard_quality.py
```

작업:

```text
- INT-001~INT-014 검사 추가
- earnings story, fed story 전용 검사 추가
- 캡처 실패 시 fallback 존재 여부 검사
- asset_queue 과다 여부 검사
```

### Phase 6 — 회고 확장

수정 대상:

```text
projects/autopark/scripts/build_broadcast_retrospective.py
projects/autopark/scripts/run_broadcast_retrospective.py
```

추가:

```text
projects/autopark/scripts/extract_ppt_outline.py
projects/autopark/scripts/build_actual_broadcast_outline.py
projects/autopark/scripts/compare_dashboard_to_broadcast_assets.py
```

작업:

```text
- 전사본뿐 아니라 PPT outline도 회고 입력으로 사용
- story hit, asset hit, sequence hit를 분리
- 다음날 feedback에 prompt update 후보와 source/asset weight update 후보를 남김
```

### Phase 7 — 샘플 테스트

테스트 날짜:

```text
2026-04-29
2026-04-30
```

테스트 목표:

```text
- 0429가 earnings_heavy로 판정되는가?
- 0429에서 earnings_education_block을 제안하는가?
- 0429에서 OpenAI 이슈를 AI 하드웨어 전체 붕괴로 오판하지 않는가?
- 0430이 fed_day + earnings_heavy + macro_risk로 판정되는가?
- 0430에서 성장/금리/유가 삼각 구도를 one_line_market_frame으로 잡는가?
- 0430에서 FOMC 문구 변화와 금리경로 자료를 required asset으로 올리는가?
```

---

## 14. Codex에게 전달할 작업 지시문

아래 블록을 Codex 작업 시작 메시지로 사용할 수 있다.

```text
Buykings repo의 projects/autopark를 보강해 주세요.
목표는 Autopark를 단순 뉴스 요약/Notion 발행기가 아니라,
위폴 7:20 아침방송용 편집장 + PPT 자료 큐 + 방송 후 회고 학습기로 발전시키는 것입니다.

참고 문서:
- projects/autopark/docs/editorial-policy/01-morning-routine.md
- projects/autopark/docs/editorial-policy/02-signal-noise-lead-selection.md
- projects/autopark/docs/editorial-policy/03-source-roles.md
- projects/autopark/docs/editorial-policy/04-market-map-checklist.md
- projects/autopark/docs/editorial-policy/05-codex-handoff-runbook.md

우선순위:
1. config/editorial_policy_manifest.yml, config/broadcast_modes.yml, config/visual_asset_manifest.yml, config/source_roles.yml 추가
2. build_market_radar.py 출력에 source_roles, signal_axes, signal_or_noise, expectation_gap, broadcast_stage, talk_vs_slide, asset_needs 추가
3. build_editorial_brief.py 프롬프트와 JSON schema에 broadcast_mode, one_line_market_frame, broadcast_rundown, ppt_asset_queue, talk_only_queue, drop_list 추가
4. build_live_notion_dashboard.py에 방송 모드, 3분 시장 지도, 추천 방송 순서, PPT 후보 자료 큐 렌더링 추가
5. review_dashboard_quality.py에 INT-001~INT-014 게이트와 earnings/fed 전용 게이트 추가
6. build_broadcast_retrospective.py를 전사본 + PPT outline + dashboard 비교 구조로 확장
7. extract_ppt_outline.py, build_actual_broadcast_outline.py, compare_dashboard_to_broadcast_assets.py 초안 추가

중요 제약:
- 공개 repo에 실제 방송 PPT/전사본 원문을 커밋하지 마세요. runtime/samples 또는 git-ignored 경로에만 둡니다.
- X/Reddit 자료는 단독 fact_anchor로 쓰지 마세요.
- 모델이 진행자의 사적인 농담이나 말투를 흉내 내지 않게 하세요. host_personalization_slot만 둡니다.
- 사용자가 보는 Notion에는 내부 점수, 클러스터 수, 프롬프트 로직을 노출하지 마세요.
- 기존 publish 동작은 dry-run과 quality gate를 통과하기 전까지 바꾸지 마세요.
```

---

## 15. 최종 산출물의 Definition of Done

Codex 작업이 완료되었다고 볼 수 있는 기준은 다음과 같다.

### 15.1 편집장 산출물

```text
- editorial-brief.json에 broadcast_mode가 있다.
- daily_thesis가 원인 + 시장 반응 + 방송 관점을 포함한다.
- storylines는 3~5개이며, 약한 후보를 억지로 채우지 않는다.
- 각 storyline에 signal_or_noise와 talk_vs_slide가 있다.
- slide_required storyline에는 ppt_asset_queue가 연결되어 있다.
- evidence_to_use는 당일 item_id를 참조한다.
- evidence_to_drop에는 drop_code가 있다.
```

### 15.2 Notion 산출물

```text
- 상단에서 오늘의 핵심 질문과 방송 모드가 바로 보인다.
- 3분 시장 지도 카드가 있다.
- 추천 방송 순서가 있다.
- PPT 후보 자료 큐가 있다.
- 말로만 처리할 자료와 버릴 자료가 분리되어 있다.
- 진행자가 바로 PPT 제작 여부를 판단할 수 있다.
```

### 15.3 시각 자료 산출물

```text
- 고정 시장 차트/히트맵/매크로 자료가 모드에 맞게 준비된다.
- 실적 시즌에는 earnings card와 stock chart pack이 준비된다.
- Fed day에는 statement diff와 rate path/FedWatch 자료가 준비된다.
- 캡처 실패 시 fallback이 있다.
- 내부 증빙 캡처와 PPT 후보 캡처가 분리된다.
```

### 15.4 품질 게이트

```text
- 필수 섹션 누락을 잡는다.
- slide_required인데 asset이 없는 경우를 잡는다.
- X/Reddit 단독 fact anchor를 잡는다.
- 실적 카드의 숫자 부족을 잡는다.
- Fed day의 정책 자료 부족을 잡는다.
- 내부 점수/클러스터 로직 노출을 잡는다.
- 과도한 asset_queue를 경고한다.
```

### 15.5 회고 루프

```text
- 실제 방송 전사본과 PPT outline을 모두 입력으로 쓴다.
- 추천 스토리라인 적중률과 실제 장표 사용 여부를 분리해서 평가한다.
- missed_topic뿐 아니라 missed_asset도 기록한다.
- 다음날 프롬프트에 반영할 수 있는 feedback을 남긴다.
- 회고는 자동 코드 수정이 아니라 Codex 검토용 제안으로 남는다.
```

---

## 16. 마지막 운영 원칙

Autopark가 앞으로 따라야 할 최종 원칙은 다음 한 문장이다.

```text
오늘 시장을 설명하는 가장 강한 원인을 찾고,
그 원인을 방송에서 이해시키는 데 필요한 최소한의 장표와 말할 순서를 제안하라.
```

많이 모으는 것이 목표가 아니다. 많이 보여주는 것도 목표가 아니다. 실제 방송에서는 시간이 제한되어 있고, 진행자는 이미 자신만의 말맛과 판단 감각을 갖고 있다.

Autopark는 그 감각을 대체하는 시스템이 아니라, 진행자가 새벽에 해야 하는 반복 작업을 줄이고, 놓치기 쉬운 근거와 자료를 정리해주는 조연이어야 한다.

따라서 최종 설계 방향은 다음과 같다.

```text
수집은 넓게,
판단은 좁게,
자료는 PPT 친화적으로,
문장은 방송 순서대로,
회고는 다음날 더 잘 고르기 위해.
```
