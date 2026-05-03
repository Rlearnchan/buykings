---
title: "Autopark Editorial Policy v1 — 03 Source Roles"
version: "0.1-draft"
scope: "priority_3_source_role_mapping_legacy_media_new_media_x_reddit_aggregators"
created_for: "슈카친구들 / 위폴 아침방송 자동화 대시보드"
source_basis:
  - "박종훈의 미국주식투자 레시피: 4장 지금 당장 즐겨찾기해야 할 레거시 미디어, pp.62-71"
  - "박종훈의 미국주식투자 레시피: 5장 뉴미디어로 읽는 속보와 시장 심리, pp.72-100"
  - "보조 참조: 11장 하루 30분 루틴 중 실적·정책·시장 심리 확인 채널, pp.224-226"
repo_context:
  - "buykings/projects/autopark: source collection → market-radar → editorial-brief → Notion dashboard → quality gate → retrospective"
status: "draft_for_source_registry_prompt_quality_gate_design"
copyright_note: "원문 재현이 아니라 Autopark 운영 기준으로 재구성한 요약/설계 문서"
---

# Autopark Editorial Policy v1 — 03. 소스별 역할 기준서

## 0. 한 문장 정의

Autopark의 3차 임무는 **소스를 많이 모으는 것**이 아니라, 각 소스가 방송 판단에서 맡는 역할을 명확히 태그하는 것이다.

```text
좋은 소스 분류 = 이 출처가 사실 확인용인지, 시장 반응 확인용인지, 구조 해석용인지, 심리 온도계인지, 시각 자료 후보인지 구분하는 것
```

따라서 이 문서는 `source registry`, `market-radar candidate`, `editorial_brief.evidence_to_use`, `evidence_to_drop`, `Notion dashboard source badge`, `retrospective source feedback`에 적용할 소스별 역할 기준서다.

Autopark는 모든 출처를 같은 뉴스 공급자로 취급하면 안 된다. Reuters의 한 문장과 X의 한 게시물, Bloomberg 데이터와 Reddit 게시물은 모두 “정보”지만, 방송 판단에서 쓸 수 있는 위치가 다르다.

---

## 1. 이 문서의 범위

| 구분 | 포함 여부 | 설명 |
|---|---:|---|
| 레거시 미디어 역할 | 포함 | CNBC, Yahoo Finance, Bloomberg, WSJ, Reuters, FT, MarketWatch |
| 헤드라인 집계/시장 화면 | 포함 | BizToc, Finviz News, Finviz Heatmap/Screening |
| 뉴미디어 역할 | 포함 | X, Reddit, YouTube/팟캐스트류의 일반 운영 원칙 |
| X 계정/리스트 운영 | 포함 | 계정 그룹, 리스트 구성, 캐시태그·고급검색, 노이즈 제거 |
| Reddit 커뮤니티 활용 | 포함 | r/WallStreetBets, r/stocks, r/investing 성격 분리 |
| 소스 신뢰도 모델 | 포함 | 사실 확인, 해석, 심리, 시각 자료 역할을 분리 |
| 소스 페어링 규칙 | 포함 | 단일 출처로 결론 내리지 않는 조합 규칙 |
| `source_roles.yml` 초안 | 포함 | 자동화 프로그램이 읽기 쉬운 YAML형 예시 제공 |
| 품질 게이트 | 포함 | X/Reddit 단독 근거 금지, 역할 누락 방지 등 |
| 첫 꼭지 선정 점수 | 제외 | 2번 기준서에서 정의. 이 문서는 점수에 들어갈 소스 근거를 정리 |
| 히트맵/실적 상세 해석 | 일부 포함 | 소스 역할 관점만 포함. 상세 판단은 4번 기준서에서 작성 예정 |
| 방송 후 회고 runbook 통합 | 일부 포함 | 소스 회고 라벨 후보만 제안. 최종 통합은 5단계 문서에서 작성 예정 |

---

## 2. 책에서 추출한 핵심 운영 원칙

### 2.1 “좋은 소스인가?”보다 “어디에 쓰는 소스인가?”가 먼저다

4장의 핵심은 매체별 우열이 아니라 **성격의 차이**다. CNBC, Bloomberg, WSJ, Reuters, FT, MarketWatch는 모두 미국 시장을 읽는 데 유용하지만 같은 역할을 하지 않는다.

Autopark에는 다음 원칙을 적용한다.

```text
Reuters = 팩트 앵커
CNBC = 실시간 시장 심리와 방송감
Bloomberg = 데이터·기관 시장·매크로 인프라
WSJ = 미국 정책·기업·거시 맥락의 심층 취재
FT = 글로벌 정치·경제·금융 연결성
MarketWatch = 투자자 친화적 빠른 요약
Yahoo Finance = 무료 시세·재무·대중 관심도
Finviz/BizToc = 한 화면에서 헤드라인 반복과 시장 화면 확인
X/Reddit = 속도·해석·확산·군중 심리
```

따라서 Autopark의 `source_id`에는 반드시 `source_role`이 붙어야 한다. 역할이 없는 소스는 편집장 단계에서 신뢰하기 어렵다.

### 2.2 레거시 미디어는 “팩트와 구조”, 뉴미디어는 “속도와 심리”를 준다

레거시 미디어는 기자, 편집, 기관 브랜드, 저널리즘 윤리를 바탕으로 정보를 정제한다. 뉴미디어는 팔로워 수, 영향력, 조회수, 네트워크 확산을 바탕으로 정보가 움직인다. 레거시 미디어는 보통 `팩트 → 해석 → 보도` 순서로 작동하고, 뉴미디어는 `해석 → 의도 → 확산`의 성격이 강하다.

Autopark의 운영 규칙은 다음과 같다.

```text
레거시 미디어는 사실 확인과 구조 해석의 뼈대로 쓴다.
뉴미디어는 시장이 무엇에 반응하는지, 어떤 내러티브가 퍼지는지, 어디서 과열되는지 읽는 온도계로 쓴다.
뉴미디어의 속도는 강점이지만, 팩트 검증을 대체하지 않는다.
```

### 2.3 헤드라인 반복은 중복이 아니라 “시장 관심도 신호”다

여러 매체가 동시에 같은 이슈를 반복해서 다루면, 그 이슈는 그날 시장을 움직이는 핵심 원인일 가능성이 높다. 단, 반복 횟수만으로 첫 꼭지를 결정하면 안 된다.

Autopark는 반복 헤드라인을 다음처럼 처리한다.

```text
반복 출현 → topic_cluster 생성 → 가격 반응 확인 → 팩트 앵커 확인 → 구조 해석 확인 → 방송 적합성 판단
```

즉, BizToc/Finviz/MarketWatch의 헤드라인 반복은 `topic_discovery` 신호이지, 곧바로 `fact_confirmed`가 아니다.

### 2.4 X와 Reddit은 “시장의 심리 온도계”로 쓰되, “사실의 판사”로 쓰지 않는다

5장은 뉴미디어가 시장 심리를 빠르게 보여주지만, 해석이 팩트보다 앞서가면 과잉 확신과 집단 편향을 만들 수 있다고 본다. X와 Reddit은 매우 유용하지만, 단독으로 첫 꼭지의 사실 근거가 되면 안 된다.

Autopark 적용 규칙은 다음과 같다.

```text
X/Reddit 단독 자료 = sentiment_only 또는 watch_only
X/Reddit + Reuters/Bloomberg/공식자료 확인 = usable_evidence
X/Reddit + 가격/거래량/섹터 반응 확인 = market_sentiment_evidence
X/Reddit + 공식자료 없음 + 가격 반응 없음 = drop 또는 모니터링
```

예외는 있다. 기업 CEO, 정책 당국자, 대통령·장관·중앙은행 관련 공식 계정처럼 당사자가 직접 발신한 게시물은 `direct_source`로 태그할 수 있다. 그러나 이 경우에도 해석은 별도로 검증해야 한다.

### 2.5 소스는 “증거 역할”과 “방송 역할”을 따로 가져야 한다

같은 자료라도 증거 역할과 방송 역할이 다를 수 있다.

예를 들어 CNBC 인터뷰 클립은 `market_sentiment` 또는 `quote_material`로는 좋지만, 숫자 팩트의 최종 근거로는 Reuters/공식자료보다 약할 수 있다. Finviz 히트맵은 `visual_anchor`로 훌륭하지만, 왜 섹터가 움직였는지의 원인을 단독으로 설명하지는 못한다.

따라서 모든 수집 아이템은 아래 두 필드를 분리한다.

```yaml
evidence_role: "fact_anchor | data_anchor | structural_context | sentiment_probe | visual_anchor | opinion_layer | direct_source"
broadcast_role: "lead_opening | hook | supporting_chart | context_slide | verbal_only | watch_only | drop"
```

---

## 3. Autopark 소스 역할 택소노미

### 3.1 핵심 역할 코드

| role code | 한국어 이름 | 정의 | 대표 소스 | 단독 사용 가능 여부 |
|---|---|---|---|---:|
| `fact_anchor` | 팩트 앵커 | 실제 발생 여부, 날짜, 수치, 발언, 공식 이벤트를 확인 | Reuters, 공식자료, Bloomberg, WSJ | 가능. 단 시장 해석은 별도 필요 |
| `breaking_alert` | 속보 감지 | 이슈 발생을 가장 빠르게 감지 | CNBC, Reuters, Bloomberg, X | 불가. 반드시 확인 필요 |
| `data_anchor` | 데이터 앵커 | 가격, 금리, 지표, 시세, 실적, 캘린더 등 숫자 확인 | Bloomberg, Yahoo Finance, Finviz, Investing, 공식자료 | 가능. 해석은 별도 필요 |
| `market_reaction` | 시장 반응 | 지수, 섹터, 금리, 달러, 유가, 종목 반응 확인 | Finviz, Bloomberg, Yahoo Finance, CNBC | 불가. 원인 확인 필요 |
| `structural_context` | 구조 해석 | 정책, 기업, 산업, 거시 흐름의 의미 해석 | WSJ, FT, Bloomberg, Economist | 가능. 단 최신 속보는 확인 필요 |
| `macro_policy_context` | 매크로·정책 맥락 | Fed, 재정, 무역, 규제, 지정학을 시장과 연결 | WSJ, Bloomberg, FT, Nick Timiraos, 공식자료 | 가능. 단 의견/해석 분리 필요 |
| `sentiment_probe` | 심리 탐침 | 투자자들이 무엇에 흥분하거나 불안해하는지 확인 | CNBC, X, Reddit, Yahoo 커뮤니티 | 단독 사실 근거 불가 |
| `opinion_leader` | 오피니언 리더 | 신뢰도 높은 전략가·전문가의 관점 확인 | Liz Ann Sonders, Charlie Bilello, Nick Timiraos 등 | 단독 결론 불가 |
| `retail_crowd_gauge` | 개인투자자 군중심리 | 개인 투자자 과열, 밈, 집단 관심 확인 | Reddit, X 캐시태그 | 단독 결론 불가 |
| `visual_anchor` | 시각 자료 앵커 | 방송에서 한눈에 보여줄 그림, 표, 차트 후보 | Finviz Heatmap, Wall St Engine, X filter:images | 원인 설명에는 불충분 |
| `earnings_tracker` | 실적 추적 | 실적 일정, EPS/매출, 서프라이즈, 가이던스, 어닝 반응 확인 | Investing, CNBC Market Insider, Wall St Engine, Yahoo Finance | 공식자료와 페어링 권장 |
| `headline_aggregator` | 헤드라인 집계 | 여러 매체의 반복 이슈를 한 화면에서 감지 | BizToc, Finviz News, Yahoo Finance | 단독 결론 불가 |
| `counter_narrative` | 반대 내러티브 | 주류 해석과 다른 관점, 리스크 서사 확인 | ZeroHedge, 일부 X 계정 | 단독 결론 금지 |
| `direct_source` | 직접 발신 | 정책 당국자, 기업 CEO, 공식 계정, 기관 원문 발신 | Fed, Treasury, 기업 IR, CEO X | 사실 발신은 가능. 해석 검증 필요 |

### 3.2 역할별 페어링 규칙

| 주 소스 역할 | 반드시 붙일 보조 역할 | 이유 |
|---|---|---|
| `breaking_alert` | `fact_anchor` + `market_reaction` | 속보는 틀리거나 과장될 수 있고, 시장이 실제로 반응했는지 확인해야 함 |
| `fact_anchor` | `structural_context` 또는 `data_anchor` | 사실만으로는 방송 메시지가 되지 않음 |
| `data_anchor` | `structural_context` 또는 `sentiment_probe` | 숫자가 왜 중요한지 설명해야 함 |
| `market_reaction` | `fact_anchor` + `structural_context` | 가격 반응만으로 원인을 단정하면 후행 해석이 됨 |
| `sentiment_probe` | `fact_anchor` + `data_anchor` | 심리 과열을 실제 신호로 오판하지 않기 위해 |
| `visual_anchor` | `fact_anchor` 또는 `market_reaction` | 그림은 설명을 빠르게 하지만 원인 증명은 아님 |
| `counter_narrative` | `fact_anchor` + `quality_warning` | 강한 서사는 방송감이 있지만 검증 리스크가 큼 |

---

## 4. 레거시 미디어 소스 역할표

### 4.1 요약 매핑

| source_id | 매체 | primary roles | Autopark에서 가장 좋은 용도 | 조심할 점 |
|---|---|---|---|---|
| `cnbc` | CNBC | `breaking_alert`, `market_sentiment`, `interview_clip`, `broadcast_hook` | 오늘 시장이 무엇에 반응하는지, CEO/전문가 인터뷰, 방송용 훅 | 깊은 전략 분석 부족, 자극적 헤드라인 가능 |
| `yahoo_finance` | Yahoo Finance | `data_anchor`, `retail_interest`, `headline_aggregator` | 무료 시세, 차트, 과거 실적, 대중 관심도 | 집계 뉴스 품질이 고르지 않음, 깊은 분석 부족 |
| `bloomberg` | Bloomberg | `data_anchor`, `macro_policy_context`, `institutional_flow`, `breaking_alert` | 채권·외환·원자재·거시·기관 시장 반응 | 유료 접근, 난해함, 방송용 문장으로 가공 필요 |
| `wsj` | Wall Street Journal | `structural_context`, `policy_context`, `corporate_reporting`, `fed_signal` | 미국 정책·기업·거시의 깊은 취재, Nick Timiraos 계열 Fed 해석 | 미국 중심 시각, 유료 장벽, 실시간성 약함 |
| `reuters` | Reuters | `fact_anchor`, `breaking_alert`, `geo_supply_chain_fact` | “무슨 일이 실제로 일어났나” 확인 | 해석이 얕고 딱딱함. 방송 메시지는 별도 구성 필요 |
| `ft` | Financial Times | `global_macro_context`, `political_economy`, `structural_context` | 글로벌 정치·경제·금융 연결성, 큰 흐름 | 속보와 대중성 약함, 유료 장벽, 어려움 |
| `marketwatch` | MarketWatch | `investor_friendly_summary`, `market_reaction`, `headline_digest` | 빠른 요약, 투자자 관점의 쉬운 해설 | 분석보다 요약·속보 중심, 자극적 헤드라인 가능 |
| `biztoc` | BizToc | `headline_aggregator`, `topic_discovery` | 여러 매체가 반복하는 당일 키워드 감지 | 원출처 확인 필요, 직접 근거로 쓰지 않음 |
| `finviz_news` | Finviz News | `headline_aggregator`, `ticker_discovery` | 티커별 뉴스 흐름, 반복 키워드, 종목 후보 | 원출처와 가격 반응 확인 필요 |
| `finviz_heatmap` | Finviz Heatmap | `visual_anchor`, `market_reaction`, `sector_rotation` | 오늘 시장을 한 장면으로 보여주는 자료 | 원인 설명은 별도 소스 필요 |

### 4.2 CNBC 운영 규칙

**핵심 역할**

```yaml
source_id: cnbc
primary_roles:
  - breaking_alert
  - market_sentiment
  - interview_clip
  - broadcast_hook
allowed_broadcast_use:
  - opening_hook
  - live_market_mood
  - ceo_or_analyst_quote
  - market_insider_watchlist
not_allowed_as:
  - sole_fact_anchor_for_complex_claim
  - sole_basis_for_lead_selection
required_pairing:
  - reuters_or_bloomberg_fact_check
  - market_data_reaction
```

**Autopark 적용**

CNBC는 방송형 매체이므로, Autopark에서 가장 좋은 용도는 `오늘 시장의 분위기`와 `방송감 있는 훅`이다. CEO 인터뷰, 애널리스트 코멘트, 장전·장중·장후 특징주 정리는 대시보드에서 바로 쓸 수 있다.

다만 CNBC 헤드라인은 자극적일 수 있으므로, `lead_storyline`으로 승격하려면 Reuters/Bloomberg/공식자료 중 하나로 사실을 확인하고, Finviz/Bloomberg/Yahoo 등으로 가격 반응을 확인해야 한다.

**추천 출력 필드**

```yaml
broadcast_use: "hook | quote | market_mood | market_insider_stock"
risk_flags:
  - headline_sensationalism
  - short_term_bias
verification_required: true
```

### 4.3 Yahoo Finance 운영 규칙

**핵심 역할**

```yaml
source_id: yahoo_finance
primary_roles:
  - data_anchor
  - headline_aggregator
  - retail_interest
  - basic_fundamental_lookup
allowed_broadcast_use:
  - quick_price_context
  - chart_snapshot
  - ticker_background
  - public_interest_check
not_allowed_as:
  - deep_structural_analysis
  - sole_policy_interpretation
required_pairing:
  - original_article_source
  - official_or_reuters_confirmation_for_material_facts
```

**Autopark 적용**

Yahoo Finance는 무료 데이터, 시세, 차트, 과거 실적, 종목 페이지 확인에 유용하다. Autopark에서는 `ticker_context`, `retail_attention`, `basic_numbers`에 배치한다.

단, 다양한 외부 매체 기사를 집계하므로 뉴스 품질이 균일하지 않다. 원문 출처를 따로 확인하지 않은 Yahoo 집계 기사는 `fact_anchor`로 쓰지 않는다.

### 4.4 Bloomberg 운영 규칙

**핵심 역할**

```yaml
source_id: bloomberg
primary_roles:
  - data_anchor
  - institutional_flow
  - macro_policy_context
  - breaking_alert
  - cross_asset_reaction
allowed_broadcast_use:
  - rates_fx_commodities_context
  - institutional_market_read
  - macro_driver_explanation
  - cross_asset_confirmation
not_allowed_as:
  - casual_hook_without_translation
required_pairing:
  - cnbc_or_marketwatch_for_broadcast_language
  - finviz_or_data_chart_for_visualization
```

**Autopark 적용**

Bloomberg는 채권, 외환, 원자재, 거시경제, 기관 투자자 관점의 시장 반응을 확인하는 데 강하다. Autopark에서는 `market_reaction`과 `macro_driver`를 연결할 때 우선순위를 높인다.

방송용으로는 다소 딱딱하고 난해할 수 있으므로, 편집장 단계에서 반드시 쉬운 문장으로 변환해야 한다.

**추천 변환**

```text
Bloomberg 원문 성격: 기관 투자자용 데이터·맥락
Autopark 방송 변환: “금리/달러/유가가 같이 움직였기 때문에 이 뉴스는 단순 종목 이슈가 아니라 매크로 이슈다.”
```

### 4.5 Wall Street Journal 운영 규칙

**핵심 역할**

```yaml
source_id: wsj
primary_roles:
  - structural_context
  - policy_context
  - corporate_reporting
  - fed_signal
allowed_broadcast_use:
  - why_now
  - structural_background
  - policy_or_corporate_context
  - fed_path_interpretation
not_allowed_as:
  - fastest_breaking_feed
required_pairing:
  - reuters_or_bloomberg_for_latest_fact
  - market_reaction_data
```

**Autopark 적용**

WSJ는 미국 경제, 기업, 정책 흐름의 심층 취재와 구조 해석에 강하다. 첫 꼭지의 `why_now`, `why_it_matters`, `structural_context`를 채우는 데 적합하다.

Nick Timiraos 관련 기사는 Fed 해석에서 별도 높은 우선순위를 둘 수 있다. 단, WSJ는 미국 중심 시각과 유료 장벽이 있으므로 글로벌 균형이 필요한 주제는 FT/Bloomberg와 페어링한다.

### 4.6 Reuters 운영 규칙

**핵심 역할**

```yaml
source_id: reuters
primary_roles:
  - fact_anchor
  - breaking_alert
  - geo_supply_chain_fact
  - corporate_fact
allowed_broadcast_use:
  - fact_confirmation
  - timeline_anchor
  - quote_or_number_confirmation
not_allowed_as:
  - deep_strategy_interpretation
  - sentiment_read
required_pairing:
  - structural_context_source
  - market_reaction_source
```

**Autopark 적용**

Reuters는 “실제로 무슨 일이 발생했나”를 확인하는 기본 앵커다. 특히 지정학, 공급망, 국제정치, 기업 공식 발표, 규제 이슈에서 우선적으로 확인한다.

단점은 해석이 깊지 않다는 점이다. Reuters가 확인한 사실은 방송의 뼈대가 되지만, 방송 메시지는 Bloomberg/WSJ/FT/CNBC/시장 데이터로 보강해야 한다.

**추천 사용 문장**

```text
Reuters로 사실 확인 → Bloomberg/WSJ/FT로 의미 확인 → Finviz/Bloomberg/Yahoo로 시장 반응 확인 → CNBC/X로 심리 확인
```

### 4.7 Financial Times 운영 규칙

**핵심 역할**

```yaml
source_id: ft
primary_roles:
  - global_macro_context
  - political_economy
  - structural_context
  - opinion_framework
allowed_broadcast_use:
  - global_context
  - long_term_frame
  - policy_finance_link
  - counter_to_us_centric_view
not_allowed_as:
  - sole_intraday_alert
required_pairing:
  - reuters_or_bloomberg_for_latest_fact
  - market_data_for_today_reaction
```

**Autopark 적용**

FT는 단기 속보보다 글로벌 정치·경제·금융의 연결성을 이해하는 데 강하다. 관세, 전쟁, 중국·유럽 정책, 달러, 에너지, 금융 시스템 리스크처럼 “왜 이런 흐름이 나타나는가”를 설명할 때 유용하다.

방송에서는 첫 꼭지의 첫 문장보다 중반부의 `큰 그림` 또는 `다음 리스크`로 배치하는 편이 좋다.

### 4.8 MarketWatch 운영 규칙

**핵심 역할**

```yaml
source_id: marketwatch
primary_roles:
  - investor_friendly_summary
  - market_reaction
  - headline_digest
allowed_broadcast_use:
  - quick_summary
  - accessible_explanation
  - secondary_context
not_allowed_as:
  - sole_deep_analysis
required_pairing:
  - reuters_or_bloomberg_for_fact
  - wsj_or_ft_for_depth_if_needed
```

**Autopark 적용**

MarketWatch는 “그래서 투자자는 무엇을 봐야 하는가”를 빠르게 정리하는 데 적합하다. 복잡한 이슈를 초보자도 이해하기 쉬운 방향으로 요약해주는 장점이 있다.

다만 자극적 헤드라인과 얕은 요약 가능성이 있으므로, MarketWatch 기반 자료는 `supporting_context` 또는 `accessible_summary`로 태그하고, 핵심 근거는 다른 출처와 페어링한다.

### 4.9 BizToc / Finviz News / Finviz Heatmap 운영 규칙

**핵심 역할**

```yaml
source_id: finviz
primary_roles:
  - headline_aggregator
  - visual_anchor
  - market_reaction
  - sector_rotation
  - ticker_discovery
allowed_broadcast_use:
  - today_market_one_scene
  - sector_strength_weakness
  - stock_watchlist
  - chart_candidate
not_allowed_as:
  - sole_causal_explanation
required_pairing:
  - original_article_source
  - market_driver_context
```

**Autopark 적용**

BizToc과 Finviz News는 여러 매체의 헤드라인을 한 화면에서 확인하는 `topic_discovery` 도구다. 여러 매체가 같은 뉴스를 반복할 때 `cluster_importance`를 높인다.

Finviz Heatmap은 방송에서 “오늘 시장을 한 장면으로 보여주는” 가장 강한 시각 자료 후보 중 하나다. 그러나 히트맵은 결과를 보여줄 뿐 원인을 설명하지 않는다. 따라서 히트맵 카드에는 반드시 원인 후보 출처가 붙어야 한다.

**추천 출력 구조**

```yaml
visual_candidate:
  source_id: finviz_heatmap
  visual_role: sector_rotation_snapshot
  explains:
    - which_sector_led
    - which_mega_cap_drove_index
    - breadth_or_concentration
  does_not_explain:
    - why_move_happened
  required_context_sources:
    - reuters
    - bloomberg
    - wsj_or_ft
```

---

## 5. 뉴미디어 소스 역할표

### 5.1 뉴미디어 기본 원칙

뉴미디어는 다음 세 가지를 빠르게 보여준다.

```text
1. 속도: 누가 무엇을 먼저 말했는가
2. 확산: 어떤 해석이 빠르게 퍼지는가
3. 심리: 투자자들이 무엇에 흥분하거나 불안해하는가
```

그러나 뉴미디어는 사실 확인의 최종 단계가 아니다. Autopark는 뉴미디어 자료를 기본적으로 `sentiment_probe`, `opinion_layer`, `narrative_tracker`, `visual_candidate`로 태그한다.

### 5.2 X.com 플랫폼 운영 규칙

**핵심 역할**

```yaml
source_id: x_platform
primary_roles:
  - breaking_alert
  - sentiment_probe
  - opinion_leader
  - direct_source
  - visual_anchor
  - narrative_tracker
allowed_broadcast_use:
  - market_mood
  - analyst_reaction
  - chart_or_data_image
  - direct_policy_or_ceo_message
  - narrative_spread
not_allowed_as:
  - unverified_fact_anchor
  - sole_lead_story_evidence
required_pairing:
  - reuters_or_bloomberg_or_official_confirmation
  - market_reaction_data
```

X는 고급 유료 매체보다 정보가 빠르게 돌 때가 있고, 기업 실적, 연준 발언, 정책 메시지, 전쟁·지정학 이슈가 거의 실시간으로 공유되는 공간이다. 또한 CEO, 정책 담당자, 헤지펀드 매니저, 경제학자가 언론 필터 없이 직접 발언하는 곳이다.

Autopark에서는 X를 “개인 맞춤형 Bloomberg”처럼 쓰되, 알고리즘과 노이즈를 통제해야 한다.

### 5.3 X 리스트 구성 기준

Autopark용 X 리스트는 사람의 북마크를 그대로 긁는 방식보다, 역할별 리스트로 나누는 것이 좋다.

| list_id | 리스트 이름 | 포함 대상 | Autopark 역할 |
|---|---|---|---|
| `x_news_headlines` | 뉴스 헤드라인 | Reuters, Bloomberg, CNBC, WSJ, FT, MarketWatch, 주요 기자 | 속보·반복 키워드 감지 |
| `x_macro_policy` | 매크로·정책 | Fed 관련 기자, 중앙은행 전문가, Treasury/USTR/정책 계정 | 금리·재정·무역·규제 신호 |
| `x_market_strategy` | 시장 전략가 | Liz Ann Sonders, Charlie Bilello, 대형 운용사 전략가 | 큰 방향, 수급, 장기 데이터 해석 |
| `x_data_charts` | 데이터·차트 | Wall St Engine, 차트/데이터 시각화 계정 | 방송용 그림 후보 |
| `x_earnings` | 실적·가이던스 | 실적 요약, 기업별 애널리스트, Wall St Engine | 실적 시즌 후보 정리 |
| `x_company_direct` | 기업/CEO 직접 발신 | 빅테크 CEO, 기업 공식 IR, 제품 발표 계정 | 직접 발신 감지. 해석은 별도 검증 |
| `x_political_direct` | 정치·정책 직접 발신 | 대통령, 장관, 정책 당국자, Truth Social/X 미러 계정 | 정책 충격 감지. 공식 확인 필요 |
| `x_alt_narrative` | 반대 내러티브 | ZeroHedge 등 비주류/강한 서사 계정 | 리스크·반론·과열 서사 탐지 |
| `x_korea_watch` | 한국장 연결 | 원화, 반도체, 한국 수출, 아시아장 전문가 | 7:20 한국 시청자 연결점 |

**리스트 운영 원칙**

```text
리스트는 유명한 계정을 모으는 곳이 아니라 역할별 신호를 분리하는 필터다.
계정 추가 전에는 꾸준성, 콘텐츠 품질, 관점, 오류 이력, 원출처 링크 습관을 확인한다.
X 추천 알고리즘에 맡기지 말고 리스트를 Autopark의 입력 채널로 쓴다.
```

### 5.4 X 고급검색 운영 규칙

Autopark에서 자동 쿼리로 쓰기 좋은 패턴은 다음과 같다.

| 목적 | 쿼리 패턴 | 결과 역할 |
|---|---|---|
| 특정 종목 실적 반응 | `$TICKER (earnings OR revenue OR guidance) min_faves:50 filter:links` | 실적 반응, 링크 포함 게시물 |
| 특정 종목 차트/표 | `$TICKER filter:images since:YYYY-MM-DD` | 시각 자료 후보 |
| 금리 관련 공식/주요 계정 | `(from:federalreserve OR from:bloomberg OR from:NickTimiraos) "interest rates"` | Fed/금리 신호 |
| AI 테마 과열 | `AI (semiconductor OR software OR data center) -crypto min_faves:100` | 테마 확산, 심리 온도 |
| 특정 계정 S&P500 언급 | `from:wallstengine ($SPX OR S&P500)` | 데이터·차트 후보 |
| 이슈 확산 강도 | `"keyword" min_retweets:100 since:YYYY-MM-DD` | 내러티브 확산도 |
| 기사 기반 게시물만 | `"keyword" filter:links min_faves:50` | 원출처 있는 해석 |
| 영상/인터뷰 확인 | `"keyword" filter:video` | 방송 클립 후보 |

**주의**

```text
min_faves/min_retweets는 중요도 점수가 아니라 확산도 점수다.
확산도가 높아도 사실일 필요는 없다.
filter:images는 방송 자료 후보를 찾는 데 좋지만, 이미지의 원자료와 날짜를 확인해야 한다.
```

### 5.5 X 계정 그룹별 역할

| source_id | 계정/매체 | primary roles | 좋은 용도 | 조심할 점 |
|---|---|---|---|---|
| `x_kobeissi_letter` | The Kobeissi Letter | `macro_storytelling`, `data_chart`, `sentiment_frame` | 거시 지표와 시장 심리의 빠른 요약, 차트 기반 스토리 | 해석이 포함되므로 맹목 추종 금지 |
| `x_wallstengine` | Wall St Engine | `data_chart`, `earnings_tracker`, `visual_anchor`, `news_digest` | 실적 시즌 일정/평가, 차트, 핵심 뉴스 2~3줄 요약 | 원출처와 공식 실적자료 확인 필요 |
| `x_liz_ann_sonders` | Liz Ann Sonders | `market_strategy`, `macro_context`, `risk_discipline` | 거시 방향, 노동·물가·선행지표, 섹터 ETF 자금 흐름 | 특정 종목 추천보다 큰 방향 중심 |
| `x_charlie_bilello` | Charlie Bilello | `data_chart`, `historical_context`, `long_term_signal` | 차트와 역사적 사이클 비교, 장기 데이터 시각화 | 당일 속보보다는 구조·데이터 해석용 |
| `x_nick_timiraos` | Nick Timiraos | `fed_signal`, `policy_context`, `fact_centered_journalist` | FOMC, 연준 발언, 의사록, 경제지표 직후 Fed 해석 | 개인 의견처럼 보이는 내용도 WSJ/공식자료와 맥락 확인 |
| `x_zerohedge` | ZeroHedge | `counter_narrative`, `risk_alert`, `alt_sentiment` | 주류와 다른 리스크 서사, 시장 불안 심리 확인 | 선정성·검증 리스크. 단독 근거 금지 |
| `x_economist` | The Economist | `global_context`, `structural_analysis`, `policy_chart` | 글로벌 정책 흐름, 정교한 차트, 엘리트 시각 | 당일 속보보다 큰 흐름용 |
| `x_direct_ceo_policy` | CEO/정책 당국자 직접 발신 | `direct_source`, `breaking_alert`, `policy_or_company_signal` | 공식 발표보다 먼저 나오는 직접 메시지 감지 | 맥락·법적 효력·시장 해석은 별도 검증 |

### 5.6 Reddit 운영 규칙

**핵심 역할**

```yaml
source_id: reddit
primary_roles:
  - retail_crowd_gauge
  - meme_stock_watch
  - narrative_tracker
  - question_pool
allowed_broadcast_use:
  - retail_sentiment_snapshot
  - meme_or_options_frenzy
  - public_question_finder
  - narrative_temperature
not_allowed_as:
  - fact_anchor
  - valuation_evidence
  - lead_story_sole_basis
required_pairing:
  - price_volume_data
  - reuters_or_company_fact
  - options_short_interest_if_relevant
```

| subreddit | 성격 | Autopark 역할 | 조심할 점 |
|---|---|---|---|
| `r/wallstreetbets` | 고위험·고수익, 옵션, 밈 주식, 모멘텀, 집단 심리 | 개인투자자 과열·투기 심리 온도계 | 펀더멘털 분석 근거로 쓰지 않음 |
| `r/stocks` | 기업 실적, 밸류에이션, 산업 구조, 리스크 토론 | 장기 투자자 질문·논리 확인 | 품질이 게시물별로 다름 |
| `r/investing` | 자산배분, 장기 포트폴리오, 은퇴자금, 투자 철학 | 대중의 장기 관심사와 질문 확인 | 단기 시장 원인 설명에는 약함 |

**Reddit 처리 원칙**

```text
Reddit은 “무엇이 사실인가”가 아니라 “개인 투자자들이 무엇을 걱정하거나 흥분하는가”를 보는 곳이다.
밈/옵션/개별 종목 과열이 방송 소재가 되려면 가격·거래량·공매도·옵션 데이터와 함께 확인한다.
Reddit에서만 뜨겁고 외부 데이터 반응이 없으면 `retail_noise` 또는 `watch_only`로 둔다.
```

---

## 6. 소스 신뢰도와 사용 가능 범위

### 6.1 신뢰도는 “출처 등급”이 아니라 “주장 유형별 사용 가능성”이다

같은 출처라도 주장 유형에 따라 신뢰도가 달라진다. 예를 들어 X의 CEO 계정은 “CEO가 이렇게 말했다”는 사실에는 강하지만, “그 말이 기업 가치에 어떤 영향을 준다”는 해석에는 약하다. Reuters는 사실 확인에는 강하지만, 방송용 재미와 구조 해석에는 약할 수 있다.

### 6.2 claim_type별 권장 출처

| claim_type | 설명 | 권장 1차 출처 | 보조 출처 | 금지/주의 |
|---|---|---|---|---|
| `event_fact` | 어떤 일이 발생했다 | Reuters, 공식자료, Bloomberg, WSJ | CNBC | X/Reddit 단독 금지 |
| `market_price` | 가격·지수·금리·유가가 움직였다 | Bloomberg, Yahoo, Finviz, 거래소/공식 데이터 | CNBC | 기사 헤드라인만으로 단정 금지 |
| `policy_signal` | 정책 방향이 바뀌었다 | 공식자료, WSJ/Nick Timiraos, Reuters, Bloomberg | X 직접 발신 | 해석형 X 계정 단독 금지 |
| `earnings_result` | 실적/가이던스가 나왔다 | 기업 IR, Investing, Yahoo, Bloomberg, CNBC Market Insider | Wall St Engine, X | 이미지 요약표 단독 금지 |
| `structural_interpretation` | 산업/정책/거시 흐름의 의미 | WSJ, FT, Bloomberg, Economist | 전략가 X 계정 | 자극적 블로그 단독 금지 |
| `sentiment_state` | 시장 심리가 이렇다 | CNBC, X 리스트, Reddit, Yahoo 커뮤니티 | 공포탐욕지수 등 심리지표 | 심리를 사실로 표현 금지 |
| `visual_material` | 방송에 보여줄 차트/이미지 | Finviz, Bloomberg chart, X filter:images, Wall St Engine | Datawrapper | 날짜·출처·축 확인 필요 |
| `counterpoint` | 반론/다른 관점 | FT, WSJ, ZeroHedge, 전략가 계정 | Reddit | 반론을 사실처럼 단정 금지 |

### 6.3 evidence quality badge

Autopark는 각 근거에 아래 배지를 붙인다.

| badge | 의미 | 방송 사용 |
|---|---|---|
| `verified_fact` | 신뢰 출처 또는 공식자료로 확인된 사실 | 핵심 근거 가능 |
| `verified_data` | 가격/지표/실적 숫자가 확인됨 | 핵심 숫자 가능 |
| `credible_context` | 신뢰 매체의 구조 해석 | `why_now`, `why_matters` 가능 |
| `sentiment_only` | 심리·여론·확산 신호 | 훅/보조 가능. 단독 첫 꼭지 금지 |
| `visual_only` | 그림은 좋지만 원인 설명 없음 | 장표 가능. 원인 근거 필요 |
| `unverified_alert` | 속보 또는 루머 단계 | Notion에 경고 표시, 첫 꼭지 금지 |
| `counter_narrative_only` | 반대 서사이지만 검증 제한 | 반론/리스크로만 사용 |
| `needs_pairing` | 보조 출처 필요 | 편집장 브리프에서 보류 |

---

## 7. 소스 페어링 플레이북

### 7.1 속보형 이슈

```text
CNBC/X/Bloomberg 속보 감지
→ Reuters 또는 공식자료로 사실 확인
→ Bloomberg/Yahoo/Finviz로 가격 반응 확인
→ WSJ/FT/Bloomberg로 구조적 의미 확인
→ X로 심리와 확산 확인
```

**첫 꼭지 가능 조건**

```text
fact_anchor 1개 이상 + market_reaction 1개 이상 + structural_context 또는 policy_context 1개 이상
```

### 7.2 Fed·금리·경제지표 이슈

```text
공식자료/Fed 발언/경제지표 발표
→ Reuters/Bloomberg로 숫자와 즉시 반응 확인
→ Nick Timiraos/WSJ/Bloomberg로 Fed 경로 해석 확인
→ 미국 10년물, 2년물, DXY, Nasdaq, Russell2000 반응 확인
→ CNBC/X로 시장이 어떤 포인트에 반응했는지 확인
```

**필수 필드**

```yaml
macro_policy_story:
  official_or_fact_source: required
  rates_reaction: required
  equity_reaction: required
  fed_path_interpretation: required
  sentiment_check: optional_but_recommended
```

### 7.3 기업 실적·가이던스 이슈

```text
기업 IR/실적 캘린더/Investing/Yahoo로 숫자 확인
→ CNBC Market Insider 또는 Reuters로 당일 시장 반응 확인
→ Wall St Engine/X로 차트·요약표·애널리스트 반응 확인
→ Bloomberg/WSJ로 가이던스·수요·마진·CAPEX 맥락 확인
→ Finviz로 섹터/동종 기업 반응 확인
```

**주의**

실적 관련 X 이미지 요약표는 방송 자료 후보가 될 수 있지만, 공식 실적 발표나 신뢰 매체 확인 없이 핵심 숫자 근거로 쓰지 않는다.

### 7.4 지정학·공급망·에너지 이슈

```text
Reuters로 사건 사실 확인
→ Bloomberg/FT로 글로벌 시장·정책·공급망 맥락 확인
→ 유가, 달러, 금리, 방산/항공/해운/에너지 섹터 반응 확인
→ CNBC/X로 시장의 공포·확산 정도 확인
→ 한국장 연결이 있으면 원/달러, KOSPI 업종, 반도체/에너지 수입 영향 확인
```

### 7.5 섹터 로테이션·히트맵 이슈

```text
Finviz Heatmap으로 강세/약세 섹터 확인
→ Bloomberg/Yahoo로 주요 대형주와 지수 기여도 확인
→ Reuters/WSJ/Bloomberg로 원인 후보 확인
→ X 데이터/차트 계정으로 시각 자료 후보 확인
→ CNBC/MarketWatch로 투자자 친화적 설명 확인
```

**주의**

히트맵은 “오늘 시장을 한 장면으로 보여주는 자료”이지, 원인 자체가 아니다.

### 7.6 밈·개인투자자 과열 이슈

```text
Reddit/X에서 티커·내러티브 확산 감지
→ 가격·거래량·옵션·공매도 데이터 확인
→ Reuters/기업자료로 실체 있는 이벤트 확인
→ CNBC/Yahoo로 대중 관심도 확인
→ 첫 꼭지보다 보조 또는 리스크 카드로 우선 배치
```

---

## 8. `source_item` 데이터 스키마 초안

Autopark의 모든 수집 아이템은 다음 스키마를 따르는 것이 좋다.

```yaml
source_item:
  item_id: "reuters_20260502_001"
  collected_at_kst: "2026-05-02T05:08:00+09:00"
  source_id: "reuters"
  source_name: "Reuters"
  source_type: "legacy_media"
  source_role:
    - fact_anchor
    - breaking_alert
  evidence_role: "fact_anchor"
  broadcast_role: "supporting_fact"
  claim_type: "event_fact"
  topic_cluster: "fed_rate_path"
  tickers: []
  asset_classes:
    - rates
    - equities
  geography:
    - US
  headline: "short sanitized headline"
  summary_kr: "방송용 1~2문장 요약"
  key_numbers:
    - label: "10Y yield"
      value: "4.68%"
      source: "market_data"
  source_confidence: "high"
  verification_status: "verified_fact"
  requires_pairing: true
  required_pairing_roles:
    - market_reaction
    - structural_context
  paired_item_ids:
    - "bloomberg_20260502_002"
    - "finviz_20260502_heatmap"
  not_allowed_use:
    - "sole_structural_interpretation"
  risk_flags: []
  url: "https://..."
  screenshot_path: null
```

### 8.1 필수 필드

| 필드 | 필수 여부 | 이유 |
|---|---:|---|
| `source_id` | 필수 | 소스별 운영 규칙 적용 |
| `source_role` | 필수 | 편집장 단계에서 근거 역할 판단 |
| `evidence_role` | 필수 | fact/data/context/sentiment/visual 분리 |
| `claim_type` | 필수 | 어떤 주장에 쓰는 근거인지 분리 |
| `verification_status` | 필수 | 단독 사용 가능 여부 판단 |
| `requires_pairing` | 필수 | X/Reddit/집계/시각자료 오판 방지 |
| `broadcast_role` | 필수 | Notion과 스토리라인 배치에 사용 |
| `risk_flags` | 권장 | 자극적 헤드라인, 유료 장벽, 루머, 과열 등 표시 |

---

## 9. `source_roles.yml` 초안

아래는 실제 리포에 `projects/autopark/config/source_roles.yml` 같은 형태로 둘 수 있는 초안이다.

```yaml
version: "0.1-draft"
default_rules:
  x_or_reddit_cannot_be_sole_fact_anchor: true
  visual_anchor_requires_context_source: true
  headline_aggregator_requires_original_source: true
  first_lead_requires_roles:
    - fact_anchor
    - market_reaction
  recommended_first_lead_roles:
    - structural_context
    - sentiment_probe

roles:
  fact_anchor:
    description: "사실 발생 여부, 공식 수치, 발언, 이벤트 확인"
    can_support_lead: true
  breaking_alert:
    description: "속보 감지"
    can_support_lead: false
    requires_pairing: [fact_anchor, market_reaction]
  data_anchor:
    description: "가격, 지표, 실적, 캘린더 숫자 확인"
    can_support_lead: true
    requires_pairing: [structural_context]
  market_reaction:
    description: "가격과 섹터 반응 확인"
    can_support_lead: true
    requires_pairing: [fact_anchor]
  structural_context:
    description: "왜 중요한지, 구조적 의미 설명"
    can_support_lead: true
  sentiment_probe:
    description: "시장 심리와 내러티브 확산 확인"
    can_support_lead: false
    requires_pairing: [fact_anchor, data_anchor]
  visual_anchor:
    description: "방송용 차트, 히트맵, 이미지 후보"
    can_support_lead: false
    requires_pairing: [fact_anchor, market_reaction]
  counter_narrative:
    description: "주류와 다른 반론 또는 리스크 서사"
    can_support_lead: false
    requires_pairing: [fact_anchor]

sources:
  reuters:
    name: "Reuters"
    type: "legacy_media"
    roles: [fact_anchor, breaking_alert]
    confidence_by_claim:
      event_fact: high
      structural_interpretation: medium_low
      sentiment_state: low
    allowed_broadcast_roles: [supporting_fact, timeline_anchor]
    not_allowed_as: [sole_structural_interpretation]
    pairing_required_for: [lead_story, interpretation]

  cnbc:
    name: "CNBC"
    type: "legacy_broadcast"
    roles: [breaking_alert, market_sentiment, interview_clip, broadcast_hook]
    confidence_by_claim:
      event_fact: medium
      sentiment_state: high
      structural_interpretation: medium_low
    allowed_broadcast_roles: [opening_hook, quote, market_mood]
    not_allowed_as: [sole_fact_anchor_for_complex_claim]
    risk_flags: [sensational_headline, short_term_bias]

  bloomberg:
    name: "Bloomberg"
    type: "legacy_media_data"
    roles: [data_anchor, macro_policy_context, institutional_flow, breaking_alert]
    confidence_by_claim:
      event_fact: high
      market_price: high
      structural_interpretation: high
    allowed_broadcast_roles: [macro_driver, cross_asset_context]
    transform_required: "explain_in_plain_korean"

  wsj:
    name: "Wall Street Journal"
    type: "legacy_media"
    roles: [structural_context, policy_context, corporate_reporting, fed_signal]
    confidence_by_claim:
      event_fact: high
      structural_interpretation: high
      fed_policy_signal: high
    allowed_broadcast_roles: [why_now, structural_background]
    risk_flags: [us_centric_view, paywall]

  ft:
    name: "Financial Times"
    type: "legacy_media"
    roles: [global_macro_context, political_economy, structural_context]
    confidence_by_claim:
      global_context: high
      event_fact: medium_high
      intraday_alert: medium_low
    allowed_broadcast_roles: [global_context, long_term_frame]
    risk_flags: [paywall, complexity]

  marketwatch:
    name: "MarketWatch"
    type: "legacy_media"
    roles: [investor_friendly_summary, market_reaction, headline_digest]
    confidence_by_claim:
      quick_summary: high
      structural_interpretation: medium
    allowed_broadcast_roles: [accessible_summary, secondary_context]
    risk_flags: [headline_sensationalism]

  yahoo_finance:
    name: "Yahoo Finance"
    type: "finance_portal"
    roles: [data_anchor, headline_aggregator, retail_interest]
    confidence_by_claim:
      market_price: high
      basic_financials: medium_high
      external_news_fact: medium_low
    allowed_broadcast_roles: [ticker_context, basic_chart]
    requires_original_source_for_news: true

  biztoc:
    name: "BizToc"
    type: "headline_aggregator"
    roles: [headline_aggregator, topic_discovery]
    confidence_by_claim:
      topic_repetition: high
      event_fact: low
    allowed_broadcast_roles: [topic_scan]
    requires_original_source_for_news: true

  finviz_news:
    name: "Finviz News"
    type: "headline_aggregator"
    roles: [headline_aggregator, ticker_discovery]
    confidence_by_claim:
      topic_repetition: high
      event_fact: low
    allowed_broadcast_roles: [ticker_news_scan]
    requires_original_source_for_news: true

  finviz_heatmap:
    name: "Finviz Heatmap"
    type: "market_visual"
    roles: [visual_anchor, market_reaction, sector_rotation]
    confidence_by_claim:
      market_reaction: high
      causality: low
    allowed_broadcast_roles: [today_market_one_scene, sector_rotation_chart]
    requires_pairing: [fact_anchor, structural_context]

  x_platform:
    name: "X.com"
    type: "new_media"
    roles: [breaking_alert, sentiment_probe, opinion_leader, direct_source, visual_anchor]
    confidence_by_claim:
      sentiment_state: high
      direct_quote: medium_high
      event_fact: low
    allowed_broadcast_roles: [sentiment_check, analyst_reaction, visual_candidate]
    not_allowed_as: [sole_fact_anchor, sole_lead_evidence]
    list_required: true

  reddit:
    name: "Reddit"
    type: "community"
    roles: [retail_crowd_gauge, meme_stock_watch, narrative_tracker]
    confidence_by_claim:
      retail_sentiment: high
      event_fact: low
      valuation_evidence: low
    allowed_broadcast_roles: [retail_sentiment_snapshot, meme_risk]
    not_allowed_as: [fact_anchor, lead_story_sole_basis]
```

---

## 10. `market-radar`와 `editorial-brief` 적용 방식

### 10.1 topic cluster 단계

수집된 아이템은 먼저 출처가 아니라 `topic_cluster`로 묶는다.

```yaml
topic_cluster:
  id: "fed_rate_path_repricing"
  repeated_sources:
    - reuters
    - bloomberg
    - cnbc
    - x_nick_timiraos
  role_coverage:
    fact_anchor: 1
    data_anchor: 1
    structural_context: 1
    sentiment_probe: 2
    visual_anchor: 0
  coverage_badges:
    - fact_confirmed
    - market_reaction_confirmed
    - sentiment_checked
    - visual_missing
```

### 10.2 source coverage score

기존 중요도 점수와 별개로, 각 스토리라인에는 `source_coverage_score`를 둔다.

| 역할 커버리지 | 점수 |
|---|---:|
| `fact_anchor` 있음 | +25 |
| `market_reaction` 있음 | +20 |
| `data_anchor` 있음 | +15 |
| `structural_context` 있음 | +20 |
| `sentiment_probe` 있음 | +10 |
| `visual_anchor` 있음 | +10 |
| X/Reddit 단독 | -40 |
| 집계 사이트 원출처 미확인 | -25 |
| visual만 있고 원인 없음 | -20 |
| counter_narrative 단독 | -30 |

**해석**

```text
80점 이상: 첫 꼭지 후보의 근거 구조가 비교적 안정적
60~79점: 보조 꼭지 또는 확인 후 첫 꼭지 가능
40~59점: watch 또는 supporting material
40점 미만: 드롭 또는 회고용 모니터링
```

이 점수는 첫 꼭지 선정 점수 자체가 아니다. 2번 기준서의 `lead_score`에 들어가는 근거 품질 보조 점수다.

### 10.3 `editorial_brief.storylines[*]` 보강 필드

```yaml
storyline:
  id: "story_01"
  title: "금리 경로 재조정이 기술주를 눌렀다"
  lead_candidate: true
  source_coverage:
    fact_anchor:
      - item_id: "reuters_001"
        source_id: "reuters"
    data_anchor:
      - item_id: "bloomberg_rates_001"
        source_id: "bloomberg"
    market_reaction:
      - item_id: "finviz_heatmap_001"
        source_id: "finviz_heatmap"
    structural_context:
      - item_id: "wsj_fed_001"
        source_id: "wsj"
    sentiment_probe:
      - item_id: "x_nick_001"
        source_id: "x_nick_timiraos"
  source_coverage_score: 85
  source_risks:
    - "visual_anchor_does_not_prove_causality"
  missing_evidence: []
```

### 10.4 `evidence_to_use` 보강 필드

```yaml
evidence_to_use:
  - item_id: "reuters_001"
    evidence_role: "fact_anchor"
    source_role: ["fact_anchor", "breaking_alert"]
    broadcast_role: "supporting_fact"
    why_use: "사건 발생과 핵심 수치를 확인하는 기준점"

  - item_id: "finviz_heatmap_001"
    evidence_role: "visual_anchor"
    source_role: ["visual_anchor", "market_reaction"]
    broadcast_role: "opening_visual"
    why_use: "오늘 시장을 한 장면으로 보여주지만 원인 설명에는 보조 출처 필요"
```

### 10.5 `evidence_to_drop` 보강 필드

```yaml
evidence_to_drop:
  - item_id: "reddit_wsb_001"
    source_id: "reddit_wsb"
    evidence_role: "retail_crowd_gauge"
    drop_code: "sentiment_only"
    reason: "개인투자자 과열은 보이나 Reuters/Bloomberg/공식자료와 가격 반응으로 확인되지 않음"

  - item_id: "x_alt_001"
    source_id: "x_zerohedge"
    evidence_role: "counter_narrative"
    drop_code: "counter_narrative_unverified"
    reason: "반론으로 참고 가능하지만 검증된 팩트 앵커가 없음"
```

---

## 11. Notion 대시보드 표시 기준

### 11.1 소스 배지는 사용자에게 판단 근거를 보여줘야 한다

Notion의 각 스토리라인 카드에는 단순 출처 목록이 아니라 `역할 배지`를 붙인다.

| 배지 | 표시 예시 | 의미 |
|---|---|---|
| `팩트 확인` | Reuters | 사실 발생 확인 |
| `시장 반응` | Finviz Heatmap / Bloomberg | 가격·섹터·금리 반응 확인 |
| `구조 해석` | WSJ / FT / Bloomberg | 왜 중요한지 설명 |
| `심리 확인` | CNBC / X / Reddit | 시장이 어떻게 받아들이는지 확인 |
| `시각 자료` | Finviz / X image / Wall St Engine | 장표 후보 |
| `주의` | X only / Reddit only / Aggregator only | 단독 근거로 쓰면 위험 |

### 11.2 카드 템플릿

```markdown
## 추천 스토리라인 1 — [제목]

**한 줄 관점**
[오늘 시장을 설명하는 문장]

**소스 역할 매트릭스**

| 역할 | 사용 자료 | 상태 |
|---|---|---|
| 팩트 확인 | Reuters | 확인됨 |
| 시장 반응 | Finviz Heatmap, Bloomberg rates | 확인됨 |
| 구조 해석 | WSJ | 확인됨 |
| 심리 확인 | CNBC, X 리스트 | 보조 |
| 시각 자료 | Finviz Heatmap | 사용 가능 |

**주의할 점**
[X/Reddit/집계 사이트/시각자료만으로 단정하면 안 되는 부분]

**방송 배치**
오프닝: [시각 자료] → 핵심 사실: [팩트 앵커] → 왜 중요: [구조 해석] → 시장 심리: [CNBC/X]
```

### 11.3 소스 경고 문구

Notion에 아래 문구를 자동으로 붙일 수 있다.

| 조건 | 경고 문구 |
|---|---|
| X/Reddit 단독 | `주의: 심리/확산 신호일 뿐, 사실 확인 근거는 아직 부족합니다.` |
| Finviz만 존재 | `주의: 시장 반응은 보이지만 원인 설명은 별도 확인이 필요합니다.` |
| 집계 사이트만 존재 | `주의: 원출처 확인 전에는 방송 핵심 근거로 사용하지 마세요.` |
| ZeroHedge/강한 서사만 존재 | `주의: 반대 내러티브로 참고하되, 사실·데이터 확인이 필요합니다.` |
| Bloomberg/FT/WSJ만 존재하고 방송감 없음 | `주의: 구조 해석은 좋지만 방송용 훅과 시각 자료가 필요합니다.` |

---

## 12. 품질 게이트 v0.1

`review_dashboard_quality.py` 또는 별도 `review_source_roles.py`에 넣을 수 있는 규칙이다.

### 12.1 필수 게이트

| gate_id | 규칙 | 실패 처리 |
|---|---|---|
| `SRC-001` | 모든 수집 아이템에는 `source_id`와 `source_role`이 있어야 한다 | fail |
| `SRC-002` | 모든 스토리라인에는 최소 1개 `fact_anchor` 또는 `data_anchor`가 있어야 한다 | fail |
| `SRC-003` | 첫 꼭지 후보에는 `fact_anchor`와 `market_reaction`이 모두 있어야 한다 | fail |
| `SRC-004` | X/Reddit 단독 스토리라인은 첫 꼭지 후보가 될 수 없다 | fail |
| `SRC-005` | `visual_anchor`만 있는 스토리라인은 원인 설명으로 쓰면 안 된다 | fail |
| `SRC-006` | `headline_aggregator` 기반 아이템은 원출처가 없으면 `fact_anchor` 금지 | fail |
| `SRC-007` | `counter_narrative` 단독 근거는 `counterpoint` 또는 `watch_only`로만 사용 | fail |
| `SRC-008` | CNBC/MarketWatch의 자극적 헤드라인은 최소 1개 팩트 앵커로 확인해야 한다 | warn/fail |
| `SRC-009` | Bloomberg/FT/WSJ 구조 해석만 있고 시장 가격 반응이 없으면 첫 꼭지 점수 제한 | warn |
| `SRC-010` | Reddit 관련 자료는 가격·거래량·옵션·공매도 중 하나와 페어링되어야 한다 | warn/fail |
| `SRC-011` | X 이미지/차트는 원자료 날짜와 지표명을 확인해야 한다 | warn |
| `SRC-012` | 직접 발신 계정 자료는 `direct_source`로 태그하고 해석을 별도 분리해야 한다 | fail |
| `SRC-013` | 동일 테마의 중복 헤드라인은 개별 스토리로 쪼개지 말고 topic cluster로 병합 | warn |
| `SRC-014` | `source_coverage_score`가 60 미만인 스토리라인은 추천도 4점 이상 금지 | fail |
| `SRC-015` | 소스 역할이 서로 충돌하면 `source_conflict_note`를 작성 | warn |

### 12.2 첫 꼭지 전용 게이트

```text
Lead Story Source Gate
1. fact_anchor exists? yes/no
2. market_reaction exists? yes/no
3. structural_context or macro_policy_context exists? yes/no
4. sentiment_probe exists? optional
5. visual_anchor exists? optional but recommended
6. any source risk? describe
7. any X/Reddit-only claim? reject or downgrade
```

---

## 13. `build_editorial_brief.py`용 프롬프트 블록

아래 블록은 편집장 LLM 프롬프트에 그대로 넣을 수 있는 형태다.

```text
You are the Autopark editorial editor for a Korean morning market broadcast.
Do not treat all sources equally. Every evidence item has a source role.

Source role rules:
- Reuters and official sources are fact anchors. Use them to confirm what happened, not to create a full market narrative alone.
- CNBC is useful for live market mood, interviews, and broadcast hooks. Do not use it as the sole basis for complex factual claims.
- Bloomberg is strong for data, cross-asset market reaction, rates, FX, commodities, and institutional context. Translate it into plain Korean for broadcast.
- WSJ is strong for corporate, policy, and Fed-related structural context. Use it for why-now and why-it-matters.
- FT is strong for global macro, political economy, and long-term structural framing. Use it for broader context, not intraday confirmation alone.
- MarketWatch is useful for investor-friendly summaries. Pair it with fact anchors for important claims.
- Yahoo Finance is useful for price, charts, basic financial data, and aggregated headlines. Do not treat aggregated news as original confirmation.
- BizToc and Finviz News are headline aggregators. Use them for topic discovery and repeated headline detection, not as final evidence.
- Finviz Heatmap is a visual and market reaction anchor. It shows what moved, not why it moved.
- X is useful for speed, direct messages, analyst reactions, charts, and sentiment. X alone cannot be the sole fact anchor unless it is an official/direct source, and even then interpretation requires verification.
- Reddit is a retail sentiment gauge. It cannot be used as a fact anchor or valuation source.
- ZeroHedge or similar alternative-narrative sources may be used only as counter-narrative or risk-sentiment material unless independently verified.

For every storyline, produce:
1. source_coverage matrix: fact_anchor, data_anchor, market_reaction, structural_context, sentiment_probe, visual_anchor.
2. source_coverage_score from 0 to 100.
3. missing_evidence list.
4. evidence_to_use with evidence_role and broadcast_role.
5. evidence_to_drop with drop_code when an item is too weak, duplicate, sentiment-only, visual-only, or unverified.

A lead storyline must have at least:
- one fact_anchor or data_anchor,
- one market_reaction source,
- one structural_context or macro_policy_context source.

Never promote an X-only, Reddit-only, aggregator-only, or visual-only item to lead.
```

---

## 14. 회고 루프에 넘길 소스 라벨

방송 후 회고에서 “소재가 맞았는가”뿐 아니라 “어떤 소스가 실제로 도움이 되었는가”를 기록해야 한다.

```yaml
retrospective_source_labels:
  source_used_as_lead:
    description: "이 소스가 첫 꼭지 판단에 직접 기여"
  source_used_as_support:
    description: "이 소스가 보조 설명 또는 장표에 기여"
  source_used_as_hook:
    description: "이 소스가 오프닝/후킹 문장에 기여"
  source_used_as_visual:
    description: "이 소스가 장표/히트맵/차트로 사용됨"
  source_not_used_too_weak:
    description: "수집됐지만 근거가 약해 사용 안 함"
  source_not_used_too_complex:
    description: "좋은 자료지만 방송에서 풀기 복잡해 제외"
  source_not_used_low_visual_value:
    description: "시각화 가치가 낮아 제외"
  source_false_positive_sentiment:
    description: "심리 과열을 실제 시그널로 오판"
  source_false_positive_headline:
    description: "자극적 헤드라인을 과대평가"
  source_missing_fact_anchor:
    description: "흥미로운 소재였으나 팩트 확인 소스가 부족"
  source_missed_due_to_collection_gap:
    description: "해당 소스를 수집하지 못해 방송 소재를 놓침"
  source_role_error:
    description: "소스 역할을 잘못 분류하여 판단이 흐려짐"
```

### 14.1 회고 질문

```text
방송에서 실제로 쓰인 첫 꼭지의 fact_anchor는 무엇이었는가?
Autopark가 추천한 스토리라인에 source_role coverage가 충분했는가?
X/Reddit에서 과열된 소재가 실제 방송에서 쓰였는가, 아니면 노이즈였는가?
Finviz/차트 자료 중 실제 장표화된 것은 무엇인가?
좋은 소스였지만 방송에서 너무 복잡해서 제외된 자료는 무엇인가?
어떤 소스가 반복적으로 false positive를 만들었는가?
어떤 소스가 반복적으로 missed story를 막아주었는가?
```

---

## 15. Autopark 구현 우선순위

### 15.1 P0 — source registry 도입

현재 북마크/소스 목록을 아래 필드로 정리한다.

```yaml
source_id:
source_name:
source_type:
primary_roles:
allowed_claim_types:
not_allowed_as:
required_pairings:
access_method:
login_required:
failure_mode:
fallback_sources:
```

### 15.2 P1 — 모든 evidence item에 role 부여

`market-radar.json` 후보 생성 시점에 아래 필드를 추가한다.

```yaml
source_role:
evidence_role:
broadcast_role:
verification_status:
requires_pairing:
source_risk_flags:
```

### 15.3 P2 — source coverage score 추가

`build_editorial_brief.py`가 추천 스토리라인을 만들 때 단순 중요도만 보지 않고 근거 구조를 확인한다.

```text
첫 꼭지 후보는 “흥미로운가?” 이전에 “근거 역할이 충분한가?”를 통과해야 한다.
```

### 15.4 P3 — Notion에 소스 역할 매트릭스 표시

진행자가 대시보드를 볼 때 “이 자료를 왜 넣었는지” 한눈에 이해해야 한다. 따라서 각 스토리라인에 `팩트 / 데이터 / 시장 반응 / 구조 해석 / 심리 / 시각 자료` 매트릭스를 표시한다.

### 15.5 P4 — 회고에서 source feedback 수집

소스별 유용도와 오판을 누적하면, 다음 달에는 “박종훈 저자에게 실제로 먹히는 소스”와 “AI가 과대평가하는 소스”가 구분된다.

---

## 16. 박종훈 저자/제작진에게 확인할 질문

이 문서는 책 기반 운영 기준이므로, 실제 북마크와 방송 감각을 반영하려면 아래 질문을 확인해야 한다.

| 질문 | 이유 |
|---|---|
| 저자가 실제로 매일 첫 화면에서 보는 레거시 매체 순서는 무엇인가? | 수집 우선순위와 UI 배치 결정 |
| Bloomberg/WSJ/FT 유료 접근이 실제 자동화 환경에서 가능한가? | 크롤링/요약/링크 전략 결정 |
| CNBC는 기사보다 영상/인터뷰를 더 중시하는가? | 클립 수집·자막 요약 필요 여부 결정 |
| X 북마크/리스트에서 절대 놓치면 안 되는 계정은 누구인가? | `x_list_priority` 설정 |
| X에서 저자가 좋아하는 차트 계정과 싫어하는 과장 계정은 무엇인가? | visual false positive 감소 |
| Reddit은 실제 방송에서 어느 정도 활용 가능한가? | retail sentiment 카드 유지 여부 결정 |
| Finviz 히트맵은 매일 첫 화면에 고정해야 하는가, 이슈 있을 때만 보여줄 것인가? | Notion UI 우선순위 결정 |
| MarketWatch/Yahoo 같은 쉬운 요약 소스는 방송 문장화에 도움이 되는가? | `accessible_summary` 활용 여부 결정 |
| ZeroHedge류 반대 내러티브는 어느 정도까지 참고할 것인가? | counterpoint 정책 결정 |
| 소스가 충돌할 때 저자가 우선하는 판단 기준은 무엇인가? | 품질 게이트와 conflict note 설계 |

---

## 17. 3번 기준서의 결론

Autopark의 소스 전략은 “더 많은 소스를 넣자”가 아니라 다음 문장으로 정리된다.

```text
각 소스를 방송 판단에서 맡는 역할대로 배치하고, 단일 소스의 약점을 다른 역할의 소스로 보완한다.
```

레거시 미디어는 사실과 구조를 제공하고, 뉴미디어는 속도와 심리를 제공한다. Finviz와 BizToc은 반복 키워드와 시장 화면을 보여주지만, 원인을 설명하지는 않는다. X와 Reddit은 시장의 온도계를 제공하지만, 사실의 판사가 아니다.

따라서 Autopark는 모든 자료를 다음 여섯 칸에 배치해야 한다.

```text
팩트 확인 / 데이터 확인 / 시장 반응 / 구조 해석 / 심리 확인 / 시각 자료
```

이 여섯 칸이 채워진 스토리라인은 방송에서 쓰일 가능성이 높다. 반대로 한 칸만 과하게 강하고 나머지가 비어 있는 소재는 흥미로워 보여도 대시보드에서는 경고를 붙여야 한다.

---

## Appendix A. 최소 source registry CSV 컬럼

자동화 구현을 빠르게 시작하려면 아래 컬럼만으로도 충분하다.

```csv
source_id,source_name,source_type,primary_roles,allowed_claim_types,not_allowed_as,required_pairings,access_method,login_required,failure_mode,fallback_sources
reuters,Reuters,legacy_media,"fact_anchor;breaking_alert","event_fact;corporate_fact;geo_fact","deep_strategy_interpretation","market_reaction;structural_context",rss_or_web,false,rate_limit,"ap;bloomberg;cnbc"
cnbc,CNBC,legacy_broadcast,"breaking_alert;market_sentiment;interview_clip","sentiment_state;interview_quote;market_mood","sole_complex_fact_anchor","reuters_or_bloomberg;market_data",web_or_rss,false,video_or_page_change,"marketwatch;yahoo_finance"
finviz_heatmap,Finviz Heatmap,market_visual,"visual_anchor;market_reaction;sector_rotation","market_reaction;sector_strength","causality","fact_anchor;structural_context",screenshot,false,cloudflare_or_render,"barchart;yahoo_finance"
x_platform,X.com,new_media,"sentiment_probe;opinion_leader;direct_source;visual_anchor","sentiment_state;direct_quote;chart_candidate","sole_fact_anchor","fact_anchor;market_reaction",api_or_browser,true,login_or_rate_limit,"rss;legacy_media"
reddit,Reddit,community,"retail_crowd_gauge;meme_stock_watch","retail_sentiment;narrative_temperature","fact_anchor;valuation_evidence","price_volume;fact_anchor",api_or_web,false,rate_limit,"x_platform;yahoo_finance"
```

## Appendix B. `source_role` 없는 자료의 기본 처리

```text
source_role이 없는 자료는 editorial_brief에 직접 들어갈 수 없다.
수집 단계에서 알 수 없으면 role을 unknown으로 두되, 편집장 단계 전에 classify_source_role을 실행한다.
unknown 자료가 첫 꼭지 후보의 핵심 근거가 되면 품질 게이트에서 fail 처리한다.
```

## Appendix C. `classify_source_role` 간단 규칙

```python
# pseudo-code only

def classify_source_role(source_id: str, url: str, content_type: str, author: str | None) -> dict:
    if source_id in {"reuters", "ap", "official_fed", "official_treasury", "company_ir"}:
        return {"evidence_role": "fact_anchor", "requires_pairing": False}
    if source_id in {"bloomberg"}:
        return {"evidence_role": "data_anchor", "requires_pairing": False}
    if source_id in {"wsj", "ft", "economist"}:
        return {"evidence_role": "structural_context", "requires_pairing": True}
    if source_id in {"cnbc", "marketwatch"}:
        return {"evidence_role": "market_sentiment", "requires_pairing": True}
    if source_id in {"biztoc", "finviz_news", "yahoo_finance_aggregated_news"}:
        return {"evidence_role": "headline_aggregator", "requires_pairing": True}
    if source_id == "finviz_heatmap" or content_type in {"heatmap", "chart_image"}:
        return {"evidence_role": "visual_anchor", "requires_pairing": True}
    if source_id.startswith("x_"):
        return {"evidence_role": "sentiment_probe", "requires_pairing": True}
    if source_id.startswith("reddit_"):
        return {"evidence_role": "retail_crowd_gauge", "requires_pairing": True}
    return {"evidence_role": "unknown", "requires_pairing": True}
```
