# 04.29 Review-Driven Pipeline Improvements

04.29 실제 PPT 비교 후 바로 반영한 파이프라인 개선 기록이다.

추가 참고:

- 04.29 방송 텍스트 변환본: `projects/autopark/runtime/transcripts/2026-04-29/buykings-0429-transcript.txt`
- 방송 텍스트 분석: `projects/autopark/docs/0429-broadcast-transcript-analysis.md`

## 구현 완료

### 1. Earnings Whispers 티커 pool 추출

스크립트:

- `projects/autopark/scripts/parse_earnings_calendar_tickers.py`

입력:

- `projects/autopark/data/processed/YYYY-MM-DD/earnings-calendar-x-posts.json`

출력:

- `projects/autopark/data/processed/YYYY-MM-DD/earnings-calendar-tickers.json`
- `projects/autopark/runtime/notion/YYYY-MM-DD/earnings-calendar-tickers.md`

04.29 테스트 결과:

- 41개 티커 추출.
- `HOOD`, `STX`, `TER` 등 실제 PPT 후보가 pool에 포함됨.
- 티커 태그를 `megacap`, `ai_infra`, `platform`, `consumer`, `energy`로 1차 분류.

### 2. Earnings ticker drilldown 장부

스크립트:

- `projects/autopark/scripts/build_earnings_ticker_drilldown.py`

기능:

- 캘린더 순서, 티커 태그, 기존 뉴스/X 후보, Finviz 캡처/뉴스를 합쳐 `drilldown / watch / backlog`로 분류.
- 04.29 기준 `STX`, `HOOD`, `TER`가 자동으로 깊게 볼 후보에 들어가도록 보정.
- 04.29 방송 텍스트 분석 후 score v2를 반영했다. 새 점수축은 `theme_proof`, `expectation_risk`, `operating_proof`, `business_model_shift`, `financial_quality`, `read_through`.
- Earnings Whispers 캘린더에 없더라도 Finviz 특징주/실적 뉴스에서 실적 후보가 잡히면 보조 row로 합친다. 이 덕분에 `SBUX`가 drilldown에 들어온다.
- 각 티커에 `broadcast_question`, `dashboard_slot`, `score_breakdown`, `broadcast_axes`를 남긴다.

04.29 테스트 출력:

- `projects/autopark/data/processed/2026-04-29/earnings-ticker-drilldown.json`
- `projects/autopark/runtime/notion/2026-04-29/earnings-ticker-drilldown.md`

핵심 확인:

- `STX`: score `36`. AI 스토리지 수요, Finviz 뉴스, 재무 품질/연쇄 해석/테마 증명으로 강한 drilldown.
- `SBUX`: score `32`. 캘린더에는 없지만 Finviz 실적 뉴스에서 보조 후보로 추가. 방송 질문은 “턴어라운드가 슬로건이 아니라 운영 지표로 확인되는가?”
- `HOOD`: score `20`. X 후보 연결 + 플랫폼/비즈니스 모델 변화 축으로 drilldown.
- `TER`: score `19`. 상세 뉴스는 아직 부족하지만 캘린더 상단 + AI 인프라 + 기대감/가이던스 리스크 축으로 drilldown.
- `NXPI`: 04.29 Earnings Whispers pool에는 없어서 별도 실적 소스 보강 필요.

### 3. X source profile 분리

스크립트:

- `projects/autopark/scripts/collect_x_timeline.mjs`

추가 옵션:

- `--source-profile core`
- `--source-profile market`
- `--source-profile macro`
- `--source-profile market_radar`
- `--source-profile earnings`
- `--source-profile side_dish`
- `--source-profile expanded`

신규 config 후보:

- `x-unusualwhales`
- `x-deitaone`
- `x-reuters`
- `x-bloomberg`
- `x-wsj`
- `x-ft`
- `x-ap`
- `x-cnbc`

04.29 dry-run:

```bash
node projects/autopark/scripts/collect_x_timeline.mjs --dry-run --source-profile earnings --date 2026-04-29 --max-posts 1 --scrolls 0
```

결과:

- Stocktwits에서 `$HOOD` earnings miss 포착.
- StockMarket.News에서 Paul Tudor Jones의 stock market cap/GDP 코멘트 포착. 실제 PPT의 `닷컴버블과 현재` 마무리와 가까운 소재.
- `fixed-earnings-calendar`는 lookback 24h에서는 잡히지 않았으므로 주간 캘린더 고정 수집은 계속 별도 명령에서 `lookback-hours 240`을 써야 함.
- `side_dish`는 유명인 직접 계정보다 Reuters, Bloomberg, WSJ, FT, AP, CNBC, Economist 같은 공개 X 헤드라인을 우선 훑는다. 유명인 소식도 매체 계정에서 잡힌 헤드라인이 더 정제되어 있기 때문이다.

`market_radar`는 실적보다 “시장이 지금 보고 있는 소재”를 먼저 잡기 위한 프로필이다. 현재 포함 계정은 Kobeissi, Wall St Engine, StockMarket.News, Bespoke, Charlie Bilello, Liz Ann Sonders, Kevin Gordon, Reuters, Bloomberg, CNBC다. 04.29 테스트에서는 Kobeissi의 유가/위험선호 축, Bloomberg의 UAE/OPEC 축, CNBC의 OpenAI/Amazon 축이 잡혔다. Wall St Engine은 계정 페이지 방식에서 0건이 나와 X 검색 URL fallback을 붙였다. 다만 `from:wallstengine` 검색 fallback 테스트에서도 0건이어서, 다음 단계에서는 headed 디버그 또는 X 검색 결과 DOM 전용 추출을 따로 확인해야 한다.

### 3-1. Market radar 장부

스크립트:

- `projects/autopark/scripts/build_market_radar.py`

기능:

- 뉴스, X, IsabelNet/시각자료를 합쳐 방송 소재 후보를 `추천 스토리라인 후보`, `시장 배경/리스크`, `단신/환기`, `시장 레이더 -> 필요시 특징주` 슬롯으로 나눈다.
- Kobeissi, Wall St Engine, IsabelNet은 핵심 소스로 높은 가중치를 둔다.
- 테마는 `AI/인프라`, `시장 포지셔닝/밸류에이션`, `금리/매크로`, `에너지/지정학`, `실적 신호`, `단신/환기`로 태깅한다.
- `레이더 질문`을 붙여 “왜 시장이 이걸 보고 있나”를 바로 검토할 수 있게 한다.
- 상위 후보를 소스 다양성 기준으로 묶어 서로 독립적인 `Radar Storylines` 3개를 만든다.
- `build_live_notion_dashboard.py`는 이 결과를 `주요 뉴스 요약`, `추천 스토리라인`, `오늘의 이모저모`의 `Market Radar 연결 자료`로 배치한다. 위에서는 자료명을 code text로 짚고, 실제 이미지/원문은 아래 자료 섹션에 둔다.

04.29 테스트 출력:

- `projects/autopark/data/processed/2026-04-29/market-radar.json`
- `projects/autopark/runtime/notion/2026-04-29/market-radar.md`

04.29 확인:

- UAE/OPEC, Hormuz blockade, oil $100-$105, retail call option/risk appetite, Paul Tudor Jones의 market cap/GDP, OpenAI/Amazon, IsabelNet 포지셔닝 자료가 한 장부에 잡힌다.
- 이 장부는 실적/특징주 장부보다 앞에서 돌려야 한다. 먼저 오늘 시장의 관찰 대상을 잡고, 그 다음 필요할 때 개별 티커를 내려가는 구조가 더 방송 제작자 사고방식에 가깝다.

### 4. 독립 꼭지형 스토리라인 원칙

수정:

- `projects/autopark/scripts/select_storylines_v3.py`
- `projects/autopark/scripts/select_storylines_v4.py`

새 원칙:

- `추천 스토리라인 1/2/3`은 하나의 이슈를 3막으로 전개하는 구조가 아니라, 서로 다른 방송 꼭지 후보 3개여야 한다.
- 예: `실적/특징주`, `시장 톤`, `정책·지정학/단신`.

### 5. 품질 리뷰 게이트 보강

수정:

- `projects/autopark/scripts/review_dashboard_quality.py`

새 경고:

- `스토리라인 꼭지 다양성 부족`

04.29 기존 대시보드 재검토 결과:

- gate: `pass`
- medium findings:
  - 러셀2000 히트맵 누락
  - 스토리라인 꼭지 다양성 부족

### 6. Finviz drilldown 캡처 계획

스크립트:

- `projects/autopark/scripts/prepare_finviz_drilldown_capture.py`

기능:

- `earnings-ticker-drilldown.json`에서 `drilldown` 후보를 읽어 Finviz 캡처 티커 목록을 만든다.
- 기본 후보 수는 14개로 둔다. 04.29 실제 PPT에 들어간 `TER`가 상위 10개 컷에서는 밀려났기 때문에, 실적 캘린더 상단부의 AI/플랫폼 후보를 조금 넓게 잡는 편이 낫다.
- 기본 실행은 캡처를 돌리지 않고 계획 파일만 만든다. 브라우저 캡처까지 실행하려면 `--execute`를 붙인다.

04.29 테스트 출력:

- `projects/autopark/data/processed/2026-04-29/finviz-drilldown-capture-plan.json`
- `projects/autopark/runtime/notion/2026-04-29/finviz-drilldown-capture-plan.md`

04.29 후보:

- `STX`, `META`, `HOOD`, `SPOT`, `MSFT`, `AMZN`, `SOFI`, `CLS`, `BE`, `AAPL`, `TER`, `GOOGL`, `V`, `WDC`

### 7. 단신/환기 소재 장부

스크립트:

- `projects/autopark/scripts/build_side_dish_candidates.py`

기능:

- X/뉴스 후보 중 메인 thesis로 과대평가하면 안 되는 오프닝/전환/마무리용 소재를 별도 장부로 분리한다.
- 현재 태그는 `tech_ceo`, `political_theater`, `market_anecdote`, `geopolitical_quote`.
- 태그가 없는 실적/특징주 후보는 제외한다. `HOOD` 같은 실적 티커는 `earnings-ticker-drilldown`이 담당한다.

04.29 테스트 확인:

- Paul Tudor Jones의 stock market cap/GDP 코멘트가 `market_anecdote`로 잡힘. 실제 PPT의 `닷컴버블과 현재`와 가까운 소재.
- Trump/Iran 관련 X 단신은 잡히지만, UAE/OPEC처럼 메인으로 과대평가하지 않도록 별도 섹션에 둠.

### 8. 0422식 발행용 조립기 보강

수정:

- `projects/autopark/scripts/build_live_notion_dashboard.py`

기능:

- `자료 수집` 아래에 `시장은 지금`, `오늘의 이모저모`, `실적/특징주`를 분리해 0421/0422식 구조로 조립한다.
- 추천 스토리라인에서는 이미지를 직접 소개하지 않고, 하단 자료 카드 제목을 code text로 참조한다.
- 스토리라인별 `정리 슬라이드 초안`을 넣어 PPT의 텍스트-only 슬라이드 전환을 준비한다.
- 실적 캘린더 기반 drilldown과 단신/환기 소재 후보를 발행용 구조에 배치한다.

04.29 테스트:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/build_live_notion_dashboard.py --date 2026-04-29 --output /tmp/autopark-0429-dashboard-v2.md
projects/autopark/.venv/bin/python projects/autopark/scripts/review_dashboard_quality.py --date 2026-04-29 --input /tmp/autopark-0429-dashboard-v2.md --json
```

결과:

- format score: `100`
- content score: `92`
- gate: `pass`
- 남은 경고 1개: UAE/OPEC을 메인으로 잡을 경우 증거 장표가 부족함. 이는 조립기 문제가 아니라 당시 선별/자료 보강 문제로 기록.

### 9. Finviz crop 보정

수정:

- `projects/autopark/scripts/capture_finviz_feature_stocks.mjs`

기능:

- 일봉 canvas 캡처 시 위쪽 여백을 기존보다 넓혀 ticker/상단 정보/핫뉴스 한 줄이 포함될 가능성을 높였다.
- 아래쪽 여백도 늘려 PPT에 들어간 Finviz 캡처처럼 조금 더 세로가 있는 이미지를 만든다.

## 다음 구현 후보

1. `build_earnings_ticker_drilldown.py`를 v2로 올려 `theme proof`, `expectation risk`, `operating proof`, `business model shift`, `financial quality`, `read-through`를 점수화한다.
2. Yahoo/Finviz/IR에서 `TER`, `NXPI`, `HOOD`, `STX`, `SBUX` 같은 drilldown 티커의 실적 bullet을 자동 생성한다.
3. `select_storylines_v4.py` 또는 v5에서 `daily thesis builder`를 먼저 만들고, 가장 큰 뉴스보다 “시장이 오늘 정당화해야 하는 것”을 상단 thesis로 삼는다.
4. `fixed-earnings-calendar`는 `lookback-hours 240` 같은 주간 수집으로 별도 고정 실행한다.
5. `NXPI`처럼 Earnings Whispers 이미지에서 빠진 종목을 잡기 위해 Yahoo/Investing/MarketWatch 실적 캘린더를 보조 소스로 붙인다.
6. `side_dish` profile을 실제로 한 번 넓게 돌려 Reuters/Bloomberg/WSJ/FT/AP/CNBC/Economist/DeItaone의 헤드라인 품질을 평가한다.
7. OpenAI/AI 뉴스는 `demand weakness / supply bottleneck / share shift / supplier impact` 판별 필드를 추가한다.
