# 오늘의 이모저모 자동화 계획

기준일: 2026-04-28

## Why This Matters

`2. 오늘의 이모저모`는 고정 차트보다 더 중요한 Autopark의 핵심 영역이다.

고정 차트와 특징주는 매일 같은 구조를 반복하면 되지만, 이모저모는 밤새 미국 증시와
관련해 새로 생긴 이야기, 의외의 소재, 방송에서 말이 되는 연결고리를 찾아야 한다.
즉 자동화의 목표는 단순 링크 수집이 아니라 아래 질문에 답하는 것이다.

- 밤새 무엇이 새로웠나?
- 그중 미국 증시/섹터/특징주/금리/환율/리스크 선호와 연결되는 것은 무엇인가?
- 방송 진행자가 1~2분 안에 설명할 수 있는 이야기로 묶이는가?
- 같은 이야기를 여러 소스가 반복하는지, 한 소스의 단발 주장인지 구분되는가?

## Current Inputs

현재 로컬에 있는 입력:

- `autopark/sources.xlsx`
  - 현재는 `고정` 시트 1개
  - 주요 지수, 히트맵, 10년물, 원유, 달러, 비트코인, 실적 스케줄, 공포탐욕, FedWatch 중심
  - 이모저모 전용 소스는 아직 별도 시트/분류가 없다.
- `autopark/bookmarks_26. 4. 27..html`
  - 85개 링크
  - 뉴스/리서치: Bloomberg, WSJ, CNBC, FT, MarketWatch, Reuters, FactSet Insight, Advisor Perspectives, Isabelnet, AlphaStreet
  - 시장 도구: Finviz, TradingView News, Investing, Yahoo Finance, TipRanks, ETF.com, MarketScreener, Seeking Alpha
  - X 계정: Kobeissi, StockMarket.News, Charlie Bilello, Liz Ann Sonders, Bespoke, Nick Timiraos, Stocktwits 등
  - 커뮤니티/보조: Reddit, BizToc, Flipboard, 국내 커뮤니티, 번역 도구

## Target Output

매일 아침 `오늘의 이모저모`는 아래 산출물을 만든다.

```text
data/raw/YYYY-MM-DD/today-misc/<source-id>.json
data/processed/YYYY-MM-DD/today-misc-candidates.json
data/processed/YYYY-MM-DD/storyline-drafts.json
runtime/notion/YYYY-MM-DD/today-misc.md
```

`today-misc-candidates.json`의 기본 단위:

```json
{
  "id": "source-or-cluster-id",
  "headline": "짧은 제목",
  "source_id": "reuters|cnbc|x-kobeissi|factset|...",
  "url": "https://...",
  "published_at": "2026-04-28T05:30:00+09:00",
  "captured_at": "2026-04-28T06:10:00+09:00",
  "summary": "3~5문장 요약",
  "why_it_matters": "미국 증시와 연결되는 이유",
  "market_hooks": ["금리", "AI", "실적", "달러", "중동", "소비"],
  "tickers": ["TSLA", "NVDA"],
  "evidence": [
    {"kind": "quote_or_fact", "text": "핵심 숫자/문장", "source_url": "https://..."}
  ],
  "novelty": 1,
  "market_relevance": 1,
  "broadcast_fit": 1,
  "confidence": 1,
  "needs_user_note": false
}
```

`storyline-drafts.json`은 후보를 3개 안팎의 방송용 이야기로 묶는다.

```json
{
  "storylines": [
    {
      "title": "방송용 제목",
      "one_liner": "한 줄 메시지",
      "why_today": "오늘 이걸 봐야 하는 이유",
      "supporting_items": ["candidate-id-1", "candidate-id-2"],
      "suggested_visuals": ["경제캘린더", "비트코인", "관련 티커"],
      "opening_script_draft": "진행자가 열 때 쓸 수 있는 30초 초안",
      "caveats": ["단일 소스 주장", "수치 업데이트 필요"]
    }
  ]
}
```

## Source Taxonomy

소스는 처음부터 같은 방식으로 다루지 않는다.

### 1. Fast News

목적: 밤새 새로 발생한 이벤트 확인

후보:

- Reuters
- CNBC
- Bloomberg
- WSJ
- MarketWatch
- FT
- Yahoo Finance
- TradingView News
- BizToc

처리:

- 최신 기사 목록 수집
- 제목/요약/시간/URL 추출
- 중복 기사 묶기
- paywall이면 제목/리드/검색 결과 수준까지만 보관하고 원문 전문 저장은 하지 않는다.

### 2. Research / Chart Sources

목적: 방송에서 보여줄 수 있는 “그림 되는 자료” 찾기

후보:

- FactSet Insight
- Advisor Perspectives
- Isabelnet
- Charlie Bilello blog
- Edward Jones weekly update
- BofA fund manager survey summaries
- Sector SPDR, ETF.com

처리:

- 매일 전체를 긁기보다 주기별 체크
- 새 글/차트가 있으면 후보로 저장
- 차트 이미지는 `image_refs`에 원본 URL과 로컬 저장 경로를 함께 남긴다.
- 권리/출처 표시 이슈가 있으므로 Notion/방송에는 선별된 이미지만 올리고, 전체 이미지는 내부 증빙/선별용으로 둔다.
- 나중에 Datawrapper로 재제작 가능한지 별도 판단

### 3. X / Social Signal

목적: 시장 사람들이 실제로 반응하는 소재를 조기 발견

후보:

- Kobeissi Letter
- StockMarket.News
- Charlie Bilello
- Liz Ann Sonders
- Bespoke
- Nick Timiraos
- Stocktwits
- zerohedge
- eWhispers

처리:

- X는 로그인 profile이 필요하므로 `runtime/profiles/x` 같은 persistent profile 사용
- 초기는 browser capture + visible post text 추출
- 링크/이미지/인용 트윗/조회수/시간을 저장
- 게시물 이미지는 `runtime/assets/YYYY-MM-DD/x-timeline/` 아래에 내려받고 `image_refs`에 연결한다.
- 단일 X 포스트는 confidence를 낮게 두고, Reuters/CNBC/공식 자료와 교차 확인되면 승격

### 4. Earnings / Company Event

목적: 실적, 가이던스, 컨퍼런스콜에서 방송 소재 찾기

후보:

- AlphaStreet
- Earnings Whispers
- FX Empire earnings calendar
- Yahoo Finance ticker news
- company IR

처리:

- 오늘/내일 실적 기업 목록과 밤새 발표 기업 목록 분리
- 숫자 요약보다 “왜 시장이 반응했는지”를 우선 추출
- 특징주 파이프라인과 연결하되, 이모저모에서는 스토리 후보로만 보관

### 5. Community / Curiosity

목적: 대중/커뮤니티 관심사가 시장 소재로 번지는지 감지

후보:

- Reddit
- 국내 커뮤니티
- Flipboard

처리:

- 초기에는 자동화 우선순위 낮음
- 단순 여론 확인/아이디어 보조 용도
- 출처 신뢰도는 낮게 두고, 방송 소재로 쓰려면 공식/뉴스 소스 확인 필수

## Pipeline

### Stage 0. Source Registry

`sources.xlsx`와 bookmark HTML을 바로 실행 대상으로 쓰지 않고,
먼저 `autopark/config/today_misc_sources.json`으로 정규화한다.

필드:

- `id`
- `name`
- `url`
- `category`
- `cadence`
- `requires_login`
- `auth_profile`
- `collection_method`
- `selectors_or_notes`
- `trust_level`
- `broadcast_use`
- `user_notes`

사용자가 한 소스씩 노하우를 줄 때 이 파일에 누적한다.

### Stage 1. Collect

소스별 최신 자료를 가져온다.

방법:

- RSS/API/정적 HTML이 있으면 그것을 우선
- 없으면 browser capture + DOM text extraction
- X/로그인 소스는 headed Chrome persistent profile
- paywall은 제목/리드/메타데이터 중심

원칙:

- 원문 전체를 장문 복사하지 않는다.
- URL, 제목, 시간, 핵심 발췌 위치, 요약을 저장한다.
- 캡처 이미지는 내부 증빙용으로만 저장한다.

### Stage 2. Normalize

서로 다른 소스의 결과를 같은 schema로 맞춘다.

정규화 필드:

- title
- url
- source
- published_at
- author/account
- body_text_snippet
- extracted_numbers
- mentioned_tickers
- mentioned_themes
- image_refs

### Stage 3. Triage

방송 후보로 쓸 만한 자료만 남긴다.

점수:

- `novelty`: 밤새 새로웠는가
- `market_relevance`: 미국 증시와 연결되는가
- `source_quality`: 신뢰 가능한가
- `visual_potential`: 보여줄 그림/차트가 있는가
- `broadcast_fit`: 말로 풀기 좋은가
- `follow_up_needed`: 사용자가 노하우를 줘야 하는가

초기에는 규칙 기반으로 시작한다.

예:

- 제목에 Fed, CPI, Nvidia, Tesla, AI, oil, dollar, yields, earnings, buyback, guidance가 있으면 가산
- 같은 키워드가 2개 이상 소스에서 반복되면 가산
- 단일 X 포스트인데 출처/수치가 불명확하면 감산

### Stage 4. Cluster

비슷한 후보를 하나의 이야기 묶음으로 합친다.

예:

- “AI 인프라 투자 확대” 묶음
- “금리/연준 발언” 묶음
- “테슬라 실적 이후 로보택시/FSD” 묶음
- “중동 리스크와 유가” 묶음
- “자사주 매입과 EPS 전망 개선” 묶음

### Stage 5. Draft 3 Storylines

상위 cluster에서 방송용 스토리라인 3개를 작성한다.

각 스토리라인은 아래 형식:

- 제목
- 한 줄 요약
- 왜 오늘인가
- 근거 자료 2~4개
- 같이 보여줄 차트/표
- 30초 오프닝 멘트
- 주의점

## User-Guided Onboarding Workflow

사용자가 소스별 노하우를 주는 방식은 아래가 좋다.

1. 내가 bookmark/source 후보를 5~10개 단위로 묶어 제시한다.
2. 사용자가 “이 사이트는 여기만 보면 된다”, “이건 버려도 된다”, “이 계정은 이런 소재가 좋다”를 말한다.
3. 그 내용을 `today_misc_sources.json`의 `user_notes`와 `collection_method`에 반영한다.
4. 해당 소스 1개에 대해 dry-run collect를 만든다.
5. 하루치 raw/processed 결과를 보고 precision을 고친다.
6. 안정화되면 `enabled: true`로 바꾼다.

한 번에 85개를 자동화하지 않고, 아래 순서로 온보딩한다.

### Batch A. 뉴스 골격

- Reuters
- CNBC
- Yahoo Finance
- MarketWatch
- TradingView News
- BizToc

목표: 밤새 headline 후보를 안정적으로 모은다.

### Batch B. 특수 사이트와 X 계정

- Isabelnet
- FactSet Insight
- Advisor Perspectives
- Charlie Bilello blog
- Kobeissi
- StockMarket.News
- Liz Ann Sonders
- Bespoke
- Nick Timiraos

목표: “그림 되는 자료”와 시장 참여자들이 실제로 반응하는 소재를 찾는다.
이 묶음은 사이트별 구조와 X 로그인/profile 안정성이 중요하므로, 사용자의 노하우를 받으며 하나씩 온보딩한다.

### Batch C. 실적/회사 이벤트

- AlphaStreet
- Earnings Whispers
- FX Empire earnings calendar
- Yahoo Finance ticker news
- company IR

목표: 실적 이벤트를 스토리라인 후보와 특징주 후보로 연결한다.

### Batch D. 커뮤니티/보조

- Reddit
- 국내 커뮤니티
- Flipboard

목표: 대중 관심사와 아이디어를 보조적으로 확인한다.

## First Implementation Plan

### 1. Source Importer

입력:

- `autopark/bookmarks_26. 4. 27..html`
- `autopark/sources.xlsx`

출력:

- `autopark/config/today_misc_sources.json`

처음에는 자동 분류 초안을 만들고, 사용자가 수정할 수 있게 둔다.

### 2. Candidate Collector MVP

처음 3개 소스만 선택:

- Reuters
- CNBC
- TradingView News 또는 Yahoo Finance

출력:

- `data/raw/YYYY-MM-DD/today-misc/<source>.json`
- `data/processed/YYYY-MM-DD/today-misc-candidates.json`

목표:

- 제목/URL/시간/요약 추출
- 미국 증시 관련 후보만 20개 이하로 압축

### 3. Manual Review Markdown

자동 스토리 작성 전에 사람이 보기 좋은 Markdown을 먼저 만든다.

출력:

- `runtime/notion/YYYY-MM-DD/today-misc-review.md`

형식:

```text
## 후보 1. 제목
- 출처:
- 왜 중요:
- 시장 연결:
- 같이 볼 차트:
- 사용자 확인 필요:
```

### 4. Storyline Draft MVP

리뷰 후보를 기반으로 3개 story draft를 만든다.

초기에는 LLM 호출 없이 규칙/템플릿으로 시작하고,
후보 품질이 확인되면 OpenAI API 또는 로컬 모델을 연결한다.

### 5. Notion Integration

4/22, 4/23처럼 역구성 문서에 붙일 때는 아래 위치에 넣는다.

- `## 2. 오늘의 이모저모` 바로 아래
- 먼저 후보 카드/요약
- 그 아래 근거 링크 목록
- 필요하면 캡처/차트 이미지는 보조로 삽입

## Risks

- 뉴스 사이트의 paywall과 robots/약관 이슈
  - 원문 전문 복사 대신 제목/링크/짧은 요약/메타데이터 중심으로 보관
- X 로그인과 세션 안정성
  - persistent profile을 쓰되, 실패 시 해당 소스는 skip하고 로그 남김
- 중복 기사 과다
  - URL canonicalization, 제목 유사도, ticker/theme 기반 cluster 필요
- 단일 소스 루머
  - `confidence`와 `needs_cross_check`를 필수 필드로 둔다.
- LLM 환각
  - 스토리라인은 반드시 candidate id와 source URL을 참조하게 만든다.

## Near-Term Decision

다음 구현은 `daily runner`보다 `today_misc` MVP가 우선이다.

첫 번째 작업은 `bookmarks.html + sources.xlsx -> today_misc_sources.json` importer를 만들고,
그 결과를 사용자가 보고 “살릴 소스 / 버릴 소스 / 노하우 필요한 소스”로 나누는 것이다.

## Implementation Log

### 2026-04-28. Source importer

추가:

- `autopark/scripts/import_today_misc_sources.py`
- `autopark/config/today_misc_sources.json`

실행:

```bash
autopark/.venv/bin/python autopark/scripts/import_today_misc_sources.py
```

현재 결과:

- 전체 후보: 96개
- `fast_news`: 6개
- `fast_news_paywall`: 3개
- `research_chart_source`: 6개
- `x_social_signal`: 19개
- `earnings_company_event`: 2개
- `market_tool`: 10개
- `community_curiosity`: 6개
- `workflow_tool`: 8개
- `fixed_reference`: 11개
- `unclassified`: 25개

처음부터 모두 enable하지 않고, `enabled: false`와 `onboarding_status: needs_user_review`로 둔다.
다음 단계는 Batch A의 fast news 소스 중 3개를 골라 dry-run collector를 만드는 것이다.

### 2026-04-28. Batch A collector MVP

추가:

- `autopark/scripts/collect_today_misc.py`

실행:

```bash
autopark/.venv/bin/python autopark/scripts/collect_today_misc.py --date 2026-04-28
```

현재 기본 수집 대상:

- CNBC World
- Yahoo Finance
- Reuters
- TradingView News

산출물:

- `autopark/data/raw/2026-04-28/today-misc/cnbc-com-world.json`
- `autopark/data/raw/2026-04-28/today-misc/finance-yahoo-com-source.json`
- `autopark/data/raw/2026-04-28/today-misc/tradingview-com-news.json`
- `autopark/data/processed/2026-04-28/today-misc-candidates.json`
- `autopark/runtime/notion/2026-04-28/today-misc-review.md`

관찰:

- CNBC, Yahoo Finance, TradingView News는 공개 HTML에서 headline 후보 추출 가능
- Reuters 메인 페이지는 현재 HTTP 401로 실패
- TradingView News에는 Reuters headline이 일부 섞여 있어 우회 후보로 쓸 수 있음
- 단순 headline keyword 방식이라 아직 후보 품질이 거칠다.
- `ai` 같은 짧은 키워드는 단어 경계로 매칭하도록 보정했다.
- URL/제목에서 날짜를 추론해 오래된 TradingView/CNBC 링크를 일부 제외한다.

다음 보정:

- Reuters는 RSS/섹션 URL/TradingView Reuters feed 중 안정 루트 재검토
- Yahoo Finance는 개인금융/은행/카드류 링크를 계속 제외
- 후보를 중복 headline cluster로 묶기
- headline만이 아니라 기사 lead/meta description까지 추출
- Batch B의 Isabelnet/X 계정은 browser profile 기반 collector로 별도 구현

### 2026-04-28. Batch A/B strict 24h trial

직전 하루치만 받는 테스트를 위해 `--lookback-hours 24 --require-recent-signal`을 추가했다.
날짜 신호가 URL, RSS `pubDate`, 또는 `4 hours ago`/`yesterday` 같은 제목 문구에서 추론되지 않으면 후보에서 제외한다.

Batch A 실행:

```bash
autopark/.venv/bin/python autopark/scripts/collect_today_misc.py --date 2026-04-28 --run-name today-misc-batch-a --lookback-hours 24 --require-recent-signal --limit-per-source 8 --overall-limit 24
```

산출물:

- `autopark/data/raw/2026-04-28/today-misc-batch-a/`
- `autopark/data/processed/2026-04-28/today-misc-batch-a-candidates.json`
- `autopark/runtime/notion/2026-04-28/today-misc-batch-a-review.md`

관찰:

- CNBC: 79개 링크 중 8개 후보. CNBC URL의 `/YYYY/MM/DD/` 날짜가 안정적으로 잡힌다.
- TradingView News: 99개 링크 중 6개 후보. `4 hours ago`, `yesterday` 문구가 있어 strict 24h 필터와 잘 맞는다.
- Yahoo Finance: 69개 링크를 읽었지만 strict 모드에서는 0개. 공개 목록 HTML에 날짜 신호가 부족하다.
- Reuters: 메인 페이지 HTTP 401. 직접 수집보다 RSS/대체 feed/TradingView 내 Reuters headline 경유를 검토한다.

Batch B 실행:

```bash
autopark/.venv/bin/python autopark/scripts/collect_today_misc.py --date 2026-04-28 --batch-b-default --run-name today-misc-batch-b --lookback-hours 24 --require-recent-signal --limit-per-source 6 --overall-limit 24
```

산출물:

- `autopark/data/raw/2026-04-28/today-misc-batch-b/`
- `autopark/data/processed/2026-04-28/today-misc-batch-b-candidates.json`
- `autopark/runtime/notion/2026-04-28/today-misc-batch-b-review.md`

관찰:

- FactSet Insight: HTML 목록 대신 `https://insight.factset.com/rss.xml`을 사용하도록 source-specific feed를 추가했다. 10개 RSS item 중 strict 24h 후보 1개가 잡혔다.
- Isabelnet: 공개 HTML에서 링크는 많지만 날짜 신호가 없어 strict 모드에서는 0개. 사이트별 날짜 parser 또는 RSS/브라우저 추출이 필요하다.
- Advisor Perspectives: HTTP 403. 브라우저 기반 수집 또는 다른 feed가 필요하다.
- X 계정: 공개 HTML fetch로는 post link/text/time이 나오지 않는다. 로그인된 persistent browser profile 기반 collector가 필요하다.

결론:

- Batch A는 CNBC + TradingView를 먼저 안정 루트로 삼고, Yahoo는 기사 목록의 embedded JSON/metadata parser를 별도 구현한다.
- Batch B는 FactSet처럼 RSS가 있는 곳은 feed 우선으로 처리한다.
- Isabelnet, Advisor Perspectives, X는 `browser capture + DOM text extraction` 계열로 분리해야 한다.

### 2026-04-28. Computer Use reconnaissance and parser patch

Computer Use로 Chrome 화면/접근성 트리를 확인했다.

확인한 구조:

- Isabelnet
  - 목록 카드에 `APR 28 2026` 날짜, 제목, 요약, 이미지 썸네일이 모두 노출된다.
  - 공개 HTML에도 날짜 신호가 있어, 브라우저 자동화 전용으로 돌릴 필요는 낮다.
  - parser에서 nav/search 링크를 빼고 최신 blog post 링크만 남기도록 보정했다.
- Yahoo Finance
  - 화면에는 기사 카드마다 발행처와 `13m ago`, `1h ago` 같은 relative time이 붙는다.
  - 기존 anchor-only parser는 sibling time text를 버리고 있었다.
  - 임시로 Yahoo homepage의 `/economy/`, `/markets/`, `/news/`, `/sectors/` 기사 링크를 same-day 후보로 취급했다.
  - 다음 보정은 anchor 주변 sibling text 또는 embedded JSON에서 실제 relative time을 추출하는 것이다.
- Advisor Perspectives
  - urllib/curl은 HTTP 403이지만 Chrome 화면에서는 제목, 저자, 회사, 날짜, 요약이 정상 노출된다.
  - Playwright persistent profile 또는 headed browser context 수집기로 분리한다.
- X
  - 공개 화면에서도 timeline text, `6시간 전`, 이미지 링크, 조회수/좋아요/재게시가 접근성 트리에 노출된다.
  - 일반 HTTP fetch로는 0건이므로 X 전용 browser collector가 필요하다.

보정 후 strict 24h 결과:

- Batch A
  - CNBC: 8개 후보
  - Yahoo Finance: 8개 후보
  - TradingView News: 6개 후보
  - Reuters: 401
- Batch B
  - Isabelnet: 8개 후보
  - FactSet RSS: 1개 후보
  - Advisor Perspectives: 403
  - X 계정: 일반 HTTP 수집 0개

현재 산출물:

- `autopark/data/processed/2026-04-28/today-misc-batch-a-candidates.json`
- `autopark/runtime/notion/2026-04-28/today-misc-batch-a-review.md`
- `autopark/data/processed/2026-04-28/today-misc-batch-b-candidates.json`
- `autopark/runtime/notion/2026-04-28/today-misc-batch-b-review.md`

다음 구현:

- Yahoo: sibling time/issuer extraction
- Advisor Perspectives: browser collector MVP
- X: account timeline browser collector MVP
- 후보 품질 보정: nav/quote/video/low-signal article 제외, 동일 소재 cluster

### 2026-04-28. X timeline browser collector MVP

추가:

- `autopark/scripts/collect_x_timeline.mjs`

목적:

- X 계정별 visible timeline에서 최근 게시물을 가져온다.
- 일반 HTTP fetch가 아니라 Playwright persistent profile을 사용한다.
- 수집 필드:
  - status URL
  - `time[datetime]` 기준 작성 시각
  - 게시물 본문
  - 이미지 URL/개수
  - raw text

실행:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node autopark/scripts/collect_x_timeline.mjs --date 2026-04-28 --run-name x-timeline --lookback-hours 24 --max-posts 5 --scrolls 2
```

산출물:

- `autopark/data/raw/2026-04-28/x-timeline/`
- `autopark/data/processed/2026-04-28/x-timeline-posts.json`
- `autopark/runtime/notion/2026-04-28/x-timeline-review.md`

현재 결과:

- StockMarket.News: 1개
- Kobeissi Letter: 5개
- Bespoke, Liz Ann Sonders, Nick Timiraos: 0개

관찰:

- Kobeissi와 StockMarket.News는 headless persistent profile에서도 최근 게시물이 잡힌다.
- 나머지 계정은 같은 방식에서 0건이다. URL은 맞으므로 비로그인/공개 타임라인 노출 제한 또는 X의 account별 렌더링 차이로 본다.
- `--headed --browser-channel chrome`로 로그인 profile을 부트스트랩하면 성공률이 올라갈 가능성이 높다.
- 게시물 본문은 `[data-testid="tweetText"]`를 우선 사용해 계정명/반응 수치가 섞이지 않도록 했다.

X API 검토:

- X API v2에는 recent search, post lookup, user/timeline, filtered stream 계열 endpoint가 있다.
- 현재 공식 문서는 pay-per-use credit 방식이라고 안내한다.
- recent search는 최근 7일 검색이 가능하고, 15분 rate limit이 있으며 max result 100 구조다.
- 운영 안정성은 API가 가장 좋지만 developer account, App, Bearer token, credit/billing 설정이 필요하다.
- 지금 단계에서는 browser collector를 MVP로 쓰고, 서버 이전/정기 운영 전에 API token 발급 가능 여부를 재검토한다.

### 2026-04-28. Notion PoC append

추가:

- `autopark/scripts/build_today_misc_append.py`
- `autopark/scripts/append_markdown_to_notion.py`
- `autopark/runtime/notion/2026-04-28/today-misc-poc-append.md`

목적:

- 현재 수집한 Batch A, Batch B, X 후보를 Notion 날짜 문서에 실험 블록으로 반영한다.
- 4/22, 4/23 당일 자료와 섞이지 않도록 `수집 기준일: 2026-04-28` 및 PoC 안내문을 명시한다.

반영 대상:

- `26.04.22`: `350468fb878d816fa2b5f8fc75487095`
- `26.04.23`: `350468fb878d81a19650e14eb97b6b9d`

실행:

```bash
autopark/.venv/bin/python autopark/scripts/build_today_misc_append.py --date 2026-04-28
autopark/.venv/bin/python autopark/scripts/append_markdown_to_notion.py autopark/runtime/notion/2026-04-28/today-misc-poc-append.md --page-id 350468fb878d816fa2b5f8fc75487095 --page-id 350468fb878d81a19650e14eb97b6b9d --prepend-heading "오늘의 이모저모 자동 수집 PoC"
```

결과:

- 각 페이지에 121개 블록, 2개 chunk로 append 성공.
- 포함 내용:
  - Batch A 뉴스 후보 8개
  - Batch B 특수 사이트/리서치 후보 8개
  - X 타임라인 후보 6개
  - 수집 상태 메모

### 2026-04-28. Visual source image refs

사용자 피드백:

- 뉴스는 이미지가 핵심이 아니므로 제외한다.
- X, Isabelnet 등 그림이 중요한 소스는 이미지를 함께 가져와야 한다.
- 로그인 profile은 사용자가 제공할 수 있다. Reuters 등 구독권이 있는 소스는 profile 기반 수집으로 전환 가능하다.
- 수집 후 선별 단계가 필요하지만, 선별 로직은 후보 수집 안정화 이후 별도 설계한다.

구현:

- `collect_today_misc.py`
  - `Candidate.image_refs` 추가
  - Isabelnet 목록에서 이미지 URL 추출
  - 이미지 `alt`와 후보 제목이 맞는 경우에만 연결
  - 연결된 이미지를 `autopark/runtime/assets/YYYY-MM-DD/<run-name>/` 아래에 다운로드
- `collect_x_timeline.mjs`
  - X 게시물 이미지 URL을 `image_refs`로 정규화
  - 이미지를 `autopark/runtime/assets/YYYY-MM-DD/x-timeline/` 아래에 다운로드

현재 저장 결과:

- Isabelnet 이미지: `autopark/runtime/assets/2026-04-28/today-misc-batch-b/`
- X 이미지: `autopark/runtime/assets/2026-04-28/x-timeline/`

운영 메모:

- Notion에는 전체 이미지를 바로 올리지 않는다.
- 먼저 내부 assets와 후보 JSON에서 선별하고, 방송 소재로 채택된 이미지만 Notion에 업로드한다.
- 로그인 profile은 `runtime/profiles/<source-id>` 단위로 분리한다. 계정/구독 세션은 사용자가 브라우저에서 직접 로그인하고, 수집기는 해당 profile을 재사용한다.

### 2026-04-28. Visual captioning / image intelligence PoC

사용자 피드백:

- Isabelnet, X, BofA/기관 리서치류 이미지는 수집만 해서는 가치가 덜 살아난다.
- 이미지가 말하는 핵심, 차트의 맥락, 방송에서 쓸 수 있는 훅을 중간 단계에서 붙여야 한다.
- 특히 기관 리서치 이미지는 숫자/축/지표 해석이 어려우므로 OpenAI vision model로 1차 캡션을 만들고, 방송 전에는 사람이 검수한다.

추가:

- `autopark/scripts/caption_visual_assets.py`

입력:

- `autopark/data/processed/YYYY-MM-DD/today-misc-batch-b-candidates.json`
- `autopark/data/processed/YYYY-MM-DD/x-timeline-posts.json`
- 각 후보의 `image_refs[].local_path`

출력:

- `autopark/data/processed/YYYY-MM-DD/image-intel.json`
- `autopark/runtime/notion/YYYY-MM-DD/image-intel-review.md`

모델 산출 필드:

- `visual_title`
- `chart_type`
- `plain_english_caption_ko`
- `main_claim_ko`
- `key_numbers`
- `market_context_ko`
- `broadcast_hook_ko`
- `related_assets`
- `storyline_tags`
- `follow_up_questions`
- `caveats`
- `confidence`
- `needs_manual_review`

실행:

```bash
autopark/.venv/bin/python autopark/scripts/caption_visual_assets.py --date 2026-04-28 --limit 4 --dry-run
```

현재 dry-run 결과:

- 이미지 후보 4개 탐지 성공
- 로컬 이미지 파일 존재 확인
- `OPENAI_API_KEY`가 아직 `.env`에 없어 실제 vision 호출은 보류

실제 API 실행 결과:

```bash
autopark/.venv/bin/python autopark/scripts/caption_visual_assets.py --date 2026-04-28 --limit 6
```

- 이미지 후보 6개 모두 `status: ok`
- 평균적으로 이미지당 13~17초 소요
- 산출물:
  - `autopark/data/processed/2026-04-28/image-intel.json`
  - `autopark/runtime/notion/2026-04-28/image-intel-review.md`
- 후보 주제:
  - S&P 500 강세/약세 신호 인디케이터
  - AI 인프라 포트폴리오 누적 수익률
  - 시장 심리 지표의 Risk-On 이동
  - 경기민감주 포지셔닝과 EPS 성장률 괴리
  - 지정학적 이벤트 전후 S&P 500 반응
  - `Sell in May` 계절성 검토

관찰:

- `broadcast_hook_ko`, `caveats`, `follow_up_questions`는 바로 선별 회의 재료로 쓸 만하다.
- 이미지 안 수치 판독은 꽤 잘하지만, 일부는 자신 있게 읽는 경향이 있어 `needs_manual_review`를 항상 true로 유지하는 편이 안전하다.
- 제목/alt와 실제 이미지가 다른 경우가 있을 수 있으므로, 이미지-후보 매칭 검수 단계가 필요하다.
- 다음 단계는 `image-intel.json`을 오늘의 이모저모 후보와 합쳐서 “선별 후보 5~8개”와 “스토리라인 초안 3개”를 만드는 것이다.

실제 실행 조건:

```bash
OPENAI_API_KEY=... autopark/.venv/bin/python autopark/scripts/caption_visual_assets.py --date 2026-04-28 --limit 4
```

또는 상위 `.env`에 `OPENAI_API_KEY`를 추가한 뒤:

```bash
autopark/.venv/bin/python autopark/scripts/caption_visual_assets.py --date 2026-04-28 --limit 4
```

운영 메모:

- 모델에는 이미지와 함께 제목, 출처 URL, 발행 시각, 주변 텍스트를 같이 전달한다.
- 잘 안 보이는 숫자는 추정하지 말고 `caveats`와 `needs_manual_review`로 남기게 한다.
- 이 단계의 결과는 곧바로 방송 원고가 아니라 `선별`과 `스토리라인 3개 초안`의 재료다.
- 추후 Notion에는 전체 이미지가 아니라, 선별된 image-intel 후보만 “이미지 해석 후보” 또는 “스토리라인 근거” 블록으로 적재한다.

### 2026-04-28. Integrated storyline append PoC

사용자 요청:

- 일단 선별하지 않고, 수집된 뉴스/X/이미지 해석 재료를 고루 반영한다.
- 04.21 샘플과 비교하면서 `주요 뉴스 요약 -> 추천 스토리라인 -> 자료 수집` 형태의 dashboard block을 만든다.
- 4/22, 4/23 Notion 문서에 실제로 섞어본다.

추가:

- `autopark/scripts/inspect_notion_page.py`
  - Notion example page(`26.04.21`)의 block outline을 읽어 포맷 비교용 JSON으로 저장한다.
- `autopark/scripts/build_storyline_append.py`
  - Batch A 뉴스 후보, Batch B 특수 사이트 후보, X 타임라인, `image-intel.json`을 합쳐 OpenAI structured output으로 스토리라인 3개를 생성한다.
- `autopark/scripts/append_markdown_to_notion.py`
  - `--upload-images` 옵션 추가. Markdown local image를 Notion file upload로 올릴 수 있게 했다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/inspect_notion_page.py --max-depth 2 --output autopark/runtime/notion/2026-04-28/notion-0421-sample-outline.json
autopark/.venv/bin/python autopark/scripts/build_storyline_append.py --date 2026-04-28 --sample-outline autopark/runtime/notion/2026-04-28/notion-0421-sample-outline.json --limit-news 10 --limit-x 8 --limit-images 6
autopark/.venv/bin/python autopark/scripts/append_markdown_to_notion.py autopark/runtime/notion/2026-04-28/today-misc-integrated-storylines.md --page-id 350468fb878d816fa2b5f8fc75487095 --page-id 350468fb878d81a19650e14eb97b6b9d --prepend-heading "오늘의 이모저모 통합 스토리라인 PoC" --upload-images
```

산출물:

- `autopark/runtime/notion/2026-04-28/notion-0421-sample-outline.json`
- `autopark/runtime/notion/2026-04-28/today-misc-integrated-storylines.md`

Notion 반영:

- `26.04.22`: 151 blocks, 2 chunks, appended
- `26.04.23`: 151 blocks, 2 chunks, appended
- 이미지 6개는 Notion file upload 경로로 반영했다.

생성된 스토리라인:

1. `S&P 500 변동성, 과연 '전환'의 신호인가`
2. `AI 인프라 돌풍과 시장 주도 테마의 변화`
3. `실적과 포지셔닝, 그리고 조심스러운 투자자들`

관찰:

- 04.21 샘플은 `주요 뉴스 요약`, `추천 스토리라인`, `자료 수집` 순서이고, 개별 이모저모 항목은 `quote`, 출처, 작성일자, 이미지, 주요 내용으로 이어진다.
- 이번 PoC는 그 구조를 따르되, 아직 선별 전이라 `수집 재료`가 과하게 길다.
- 다음 단계는 전체 재료 append가 아니라, storylines가 참조한 재료만 자동으로 끌어와 5~8개 자료 카드로 줄이는 것이다.
- 이미지 해석 후보는 Notion에 잘 들어가지만, 방송 문서에는 원본 이미지 전부보다 “채택된 차트 + 모델 해석 + 수동검수 체크박스” 형태가 더 적합하다.

### 2026-04-28. Lightweight visual cards and selection/storyline v2

사용자 피드백:

- 사이트별 이미지는 하루 5~6개 내외일 가능성이 높다.
- Isabelnet 등은 이미지 옆에 설명글이 잘 붙어 있어 OpenAI vision caption을 매번 만들 필요는 낮다.
- 모델은 어려운 문제, 즉 `선별`과 `스토리 구상`에 우선 투입한다.

구현:

- `autopark/scripts/build_visual_cards.py`
  - Batch B의 `image_refs`를 경량 이미지 카드로 변환한다.
  - 원문 페이지의 meta/본문 문단을 가져오되, 사이트 공통 boilerplate는 제외하고 의미 있는 첫 문단을 설명으로 사용한다.
  - 기존 `image-intel.json`이 있으면 `vision_optional`로 연결하지만 기본 설명 소스는 `page`/`candidate_summary`다.
  - OpenAI vision 호출은 하지 않는다.
- `autopark/scripts/select_storylines_v2.py`
  - 뉴스, X, 경량 visual card를 합쳐 후보 풀을 만든다.
  - OpenAI structured output은 후보 5~8개 선별과 스토리라인 3개 작성에만 사용한다.
  - 모델이 storylines에서 선별되지 않은 ID를 참조하거나 URL을 변형하는 경우를 막기 위해 후처리 검증을 추가했다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/build_visual_cards.py --date 2026-04-28 --fetch-descriptions
autopark/.venv/bin/python autopark/scripts/select_storylines_v2.py --date 2026-04-28 --sample-outline autopark/runtime/notion/2026-04-28/notion-0421-sample-outline.json --selected-count 8 --limit-news 12 --limit-x 8 --limit-visuals 8
```

산출물:

- `autopark/data/processed/2026-04-28/visual-cards.json`
- `autopark/runtime/notion/2026-04-28/visual-cards-review.md`
- `autopark/data/processed/2026-04-28/storyline-selection-v2.json`
- `autopark/runtime/notion/2026-04-28/storyline-selection-v2.md`

결과:

- visual cards: 8개
- 원문 설명 fetch: 8개 성공, 0개 실패
- selection v2 후보 풀: 35개
- 최종 선별: 8개
- 스토리라인: 3개
- 검증: storylines의 `selected_item_ids`는 모두 `selected_items` 안의 ID만 참조

생성된 스토리라인:

1. `매크로 변수 급변 속 시장의 복합 반응`
2. `지정학, 공급망 충격에도 놀라운 시장 복원력`
3. `AI 랠리 내부 구조 변화와 투자자 교체 흐름`

운영 메모:

- 앞으로 vision caption은 기본값이 아니라 `needs_visual_reasoning=true`인 카드에만 선택 실행한다.
- X/특수 사이트 이미지는 수집하고, 설명은 우선 본문/alt/게시글 텍스트로 채운다.
- Notion 운영형 문서는 append 방식보다 04.21 샘플처럼 적절한 섹션에 배치해야 한다.
- 다음 단계는 `storyline-selection-v2.md`를 기존 날짜 문서의 `2. 오늘의 이모저모` 위치에 끼워 넣는 방식의 replace/insert 기능이다.

### 2026-04-28. Notion v2 append and scale notes

Notion 반영:

```bash
autopark/.venv/bin/python autopark/scripts/append_markdown_to_notion.py autopark/runtime/notion/2026-04-28/storyline-selection-v2.md --page-id 350468fb878d816fa2b5f8fc75487095 --page-id 350468fb878d81a19650e14eb97b6b9d --prepend-heading "오늘의 이모저모 선별·스토리라인 v2" --upload-images
```

결과:

- `26.04.22`: 128 blocks, 2 chunks, appended
- `26.04.23`: 128 blocks, 2 chunks, appended

현재 모델 사용 구조:

- 모델이 URL을 직접 하나씩 읽지는 않는다.
- 수집기는 Python/Playwright/HTML parser가 URL을 읽고, 모델에는 제목/출처/요약/이미지 설명/후보 ID 같은 축약 데이터만 전달한다.
- `build_visual_cards.py`는 이미지 페이지의 설명 문단을 가져오지만 모델 호출은 하지 않는다.
- `select_storylines_v2.py`만 모델을 호출하고, 이때도 후보 35개 정도의 축약 JSON을 한 번에 넣어 선별/스토리라인을 만든다.

대규모 운영 원칙:

- 하루 수백 건이 되면 URL별 모델 판별은 금지한다.
- 1차 필터는 로컬 규칙으로 처리한다.
  - 시간 필터
  - 소스 신뢰도
  - 키워드/티커
  - 중복 URL/제목 제거
  - 이미지/차트 여부
- 2차는 cluster summary로 압축한다.
  - 같은 소재를 제목 유사도, 티커, 테마, 출처군으로 묶는다.
  - 모델에는 개별 300건이 아니라 cluster 20~40개를 보낸다.
- 3차에서만 모델이 전역 선별을 한다.
  - `오늘 쓸 5~8개`
  - `보류할 패턴`
  - `3개 스토리라인`

단발성 판별 문제:

- 후보를 하나씩 독립 평가하면 “서로 묶으면 이야기가 되는 자료”를 놓칠 수 있다.
- 그래서 선별 모델은 단일 URL 판별자가 아니라, 하루 후보 전체 또는 cluster 전체를 보는 `story architect` 역할이어야 한다.
- 좋은 구조는 아래 순서다.

```text
raw items 300개
-> local normalize/filter/dedupe
-> cluster 20~40개
-> cluster별 핵심 문장/대표 URL/대표 이미지 생성
-> 모델 전역 선별: cluster 조합으로 스토리라인 3개
-> 선택된 cluster 안에서 대표 자료 5~8개만 Notion 배치
```

비용 방침:

- 기본 caption/카드 생성에는 모델을 쓰지 않는다.
- 선별/스토리 구상에는 저렴한 모델을 기본값으로 두고, 최종 문장 다듬기나 난해한 이미지에만 상위 모델을 선택한다.
- `AUTOPARK_OPENAI_MODEL`로 모델을 바꿀 수 있게 해두었고, 앞으로는 `AUTOPARK_SELECTOR_MODEL`, `AUTOPARK_WRITER_MODEL`, `AUTOPARK_VISION_MODEL`처럼 역할별로 분리하는 편이 좋다.

다음 구현:

- `cluster_candidates.py`
  - 뉴스/X/visual cards를 theme/ticker/source/headline similarity 기준으로 cluster한다.
- `select_storylines_v3.py`
  - 개별 후보가 아니라 cluster summary를 보고 선별한다.
- `publish_section_to_notion.py`
  - append 대신 04.21 샘플처럼 날짜 문서의 `2. 오늘의 이모저모` 자리에 배치한다.

### 2026-04-28. Clean recon republish for 4/22 and 4/23

문제:

- `26.04.22`, `26.04.23`에 여러 PoC append가 누적되어 문서가 읽기 어려워졌다.
- 운영형 문서는 append가 아니라 04.21 샘플처럼 적절한 섹션에 배치되어야 한다.

구현:

- `autopark/scripts/build_clean_recon_with_storyline.py`
  - 기존 `autopark/recon/26.04.22.md`, `autopark/recon/26.04.23.md`를 읽는다.
  - `## 2. 오늘의 이모저모` 섹션을 `storyline-selection-v2.md` 본문으로 교체한다.
  - clean recon 파일을 `autopark/runtime/notion/2026-04-28/clean-recon/` 아래에 만든다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/build_clean_recon_with_storyline.py autopark/recon/26.04.22.md autopark/recon/26.04.23.md --storyline autopark/runtime/notion/2026-04-28/storyline-selection-v2.md --output-dir autopark/runtime/notion/2026-04-28/clean-recon
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/clean-recon/26.04.22.md autopark/runtime/notion/2026-04-28/clean-recon/26.04.23.md
```

결과:

- 기존 `26.04.22`: archived
  - old page id: `350468fb-878d-816f-a2b5-f8fc75487095`
  - new page id: `350468fb-878d-8190-986e-e0ca106f7cea`
  - url: `https://www.notion.so/26-04-22-350468fb878d8190986ee0ca106f7cea`
  - blocks: 227, chunks: 3
- 기존 `26.04.23`: archived
  - old page id: `350468fb-878d-81a1-9650-e14eb97b6b9d`
  - new page id: `350468fb-878d-81b7-bad1-c66b5d61439a`
  - url: `https://www.notion.so/26-04-23-350468fb878d81b7bad1c66b5d61439a`
  - blocks: 235, chunks: 3

운영 메모:

- 앞으로 날짜 문서 업데이트는 가급적 clean recon 재발행 또는 section replacement로 한다.
- append는 PoC 기록을 페이지 하단에 임시로 붙일 때만 사용한다.

### 2026-04-28. 4/22 alignment to 4/21 layout

문제:

- clean recon 1차 버전은 `storyline-selection-v2.md` 전체를 `## 2. 오늘의 이모저모` 안에 넣었다.
- 04.21 샘플은 상단에 `주요 뉴스 요약`, `추천 스토리라인`이 있고, `2. 오늘의 이모저모`에는 개별 자료 카드가 들어간다.

구현:

- `autopark/scripts/build_recon_0421_format.py`
  - `storyline-selection-v2.json`에서 `dashboard_summary_bullets`, `storylines`, `selected_items`를 분리한다.
  - 상단 `# 주요 뉴스 요약`을 v2 요약으로 교체한다.
  - 상단 `# 추천 스토리라인`을 v2 스토리라인 3개로 교체한다.
  - `## 2. 오늘의 이모저모`에는 채택 재료 카드만 배치한다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/build_recon_0421_format.py autopark/recon/26.04.22.md --selection autopark/data/processed/2026-04-28/storyline-selection-v2.json --output autopark/runtime/notion/2026-04-28/0421-format/26.04.22.md
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format/26.04.22.md
```

결과:

- 기존 4/22 clean recon page archived
  - old page id: `350468fb-878d-8190-986e-e0ca106f7cea`
- 새 4/22 page published
  - new page id: `350468fb-878d-8112-9dae-f856242025c5`
  - url: `https://www.notion.so/26-04-22-350468fb878d81129daef856242025c5`
  - blocks: 159, chunks: 2

### 2026-04-28. 4/22 closer alignment to 4/21 visible format

문제:

- 1차 04.21 alignment는 상단 배치는 맞췄지만, 세부 표기가 아직 자동화 작업 로그처럼 보였다.
- 04.21 샘플은 `quote`, `출처`, `작성 일자`, 이미지, `주요 내용` 위주이고, `선정 이유:`, `확인 필요:`, `상태:` 같은 내부 필드는 보이지 않는다.
- 문서 하단의 `파이프라인 점검 메모`는 운영 문서가 아니라 내부 문서에만 남겨야 한다.

구현:

- `autopark/docs/notion-0421-format-checklist.md`에 구현 가능한 Notion 표기 체크리스트를 작성했다.
- `autopark/scripts/build_recon_0421_format.py`를 보강했다.
  - heading 1에 04.21 샘플의 이모지 섹션명을 적용한다.
  - `구성 제안`을 `슬라이드 구성`으로 맞춘다.
  - `2. 오늘의 이모저모` 카드에서 내부 필드명을 제거하고 `출처`, `작성 일자`, `주요 내용` 중심으로 렌더링한다.
  - 고정 시장 섹션에서 `필요 캡처`, `상태`, `메모`, `해석 포인트` 등 내부 필드를 제거한다.
  - WTI/브렌트, 달러인덱스/원달러/비트코인을 04.21처럼 개별 heading으로 나눈다.
  - 하단 `파이프라인 점검 메모`를 제거한다.

결과:

- 기존 4/22 04.21-format page archived
  - old page id: `350468fb-878d-8112-9dae-f856242025c5`
- 새 4/22 page published
  - new page id: `350468fb-878d-8188-b796-dc32c56e2b3e`
  - url: `https://www.notion.so/26-04-22-350468fb878d8188b796dc32c56e2b3e`
  - blocks: 132, chunks: 2

추가 HTML 대조 후 보정:

- `출처`는 HTML export처럼 보이는 텍스트 자체를 URL로 두고, 같은 URL을 link annotation으로 건다.
- `작성 일자`와 `캡처` 시각은 code annotation으로 맞춘다.
- 상단 최종 수정 문구에서 내부 설명인 `기준 준비 대시보드 역구성 초안`을 제거한다.
- 고정 시장 섹션의 `제작: Datawrapper` 노출을 제거하고 `출처` / `캡처`만 남긴다.
- republished page:
  - old page id: `350468fb-878d-8188-b796-dc32c56e2b3e`
  - new page id: `350468fb-878d-81fe-a16f-e0f8570c363e`
  - url: `https://www.notion.so/26-04-22-350468fb878d81fea16fe0f8570c363e`

### 2026-04-28. Clustered storyline v3 and 4/21-style material references

문제:

- v2는 후보를 한 번에 모델에 넣어 선별하므로, 자료들을 한눈에 묶어 보는 흐름이 약했다.
- 04.21 샘플의 `슬라이드 구성`에는 `자료 배치:  케빈 워시 최근 발언 -> 케빈 워시와 실리콘 밸리`처럼 아래 `2. 오늘의 이모저모` 자료 제목과 정확히 이어지는 참조가 있다.
- 기존 4/22는 슬라이드 흐름은 있었지만, “아래 어떤 자료를 읽으면 되는지”가 약했다.

구현:

- `autopark/scripts/cluster_today_misc.py`
  - 수집 후보를 `market_tone`, `energy_geopolitics`, `rates_fx_policy`, `ai_tech_rotation`, `earnings_company`, `other_watchlist`로 묶는다.
  - 대표 재료와 이미지를 `today-misc-clusters.json/md`로 남긴다.
- `autopark/scripts/select_storylines_v3.py`
  - 모델 입력을 개별 URL 목록이 아니라 클러스터 요약과 대표 재료로 줄인다.
  - 기본 selector 모델은 `gpt-4.1-mini`.
  - 결과는 정확히 3개 스토리라인, 6~8개 채택 재료로 제한한다.
  - 모델이 참조한 대표 재료가 `selected_items`에서 빠지면 후처리로 보강한다.
- `autopark/scripts/build_recon_0421_format.py`
  - 각 스토리라인의 `슬라이드 구성` 아래에 `자료 배치` bullet을 추가한다.
  - `자료 배치`의 code text는 아래 `2. 오늘의 이모저모` heading과 같은 제목을 사용한다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/cluster_today_misc.py --date 2026-04-28
autopark/.venv/bin/python autopark/scripts/select_storylines_v3.py --date 2026-04-28 --sample-outline autopark/runtime/notion/2026-04-28/example-0421-outline.json --selected-count 8
autopark/.venv/bin/python autopark/scripts/build_recon_0421_format.py autopark/recon/26.04.22.md --selection autopark/data/processed/2026-04-28/storyline-selection-v3.json --output autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
```

결과:

- 후보 42개 -> 클러스터 6개
- v3 선택:
  - 스토리라인 3개
  - 채택 재료 8개
- 새 4/22 page published
  - old page id: `350468fb-878d-81b3-a7ad-c986405affd6`
  - new page id: `350468fb-878d-8131-9d8d-fc30ef5f49b4`
  - url: `https://www.notion.so/26-04-22-350468fb878d81319d8dfc30ef5f49b4`
  - blocks: 134, chunks: 2

### 2026-04-28. 4/22 feature-stock cards

문제:

- 04.21 샘플은 `3. 특징주 분석`도 개별 자료 카드 형태다.
- 4/22 문서는 `ISRG`, `UAL`, 기술주 묶음 티커만 남아 있어, 상단 스토리라인/이모저모에 비해 가장 빈 섹션이었다.

구현:

- `autopark/scripts/build_feature_stock_cards.py`
  - 4/22 방송 PPT 텍스트를 내부 참조로 삼아 특징주 자료 후보를 역추적했다.
  - Notion에는 PPT 언급 없이 04.21식 자료 카드로 렌더링한다.
  - 카드 구조: `heading -> quote -> 출처 -> 캡처/작성 일자 -> 주요 내용`.
- `autopark/scripts/build_recon_0421_format.py`
  - `--feature-stocks` 옵션을 추가해 `## 3. 실적/특징주 분석` 섹션을 별도 markdown으로 교체할 수 있게 했다.

추가된 4/22 특징주 카드:

- 이번 주 실적발표 스케줄
- 인튜이티브 서지컬
- 유나이티드 에어라인
- 스페이스X IPO와 AI 인프라 부채
- 메가캡 성장주 및 기술주의 상대적 강도
- 마이크로소프트
- 팔로알토 네트웍스
- AMD
- 코인베이스
- 시스코
- 마벨 테크놀로지
- 온 세미컨덕터
- 코히런트

실행:

```bash
autopark/.venv/bin/python autopark/scripts/build_feature_stock_cards.py --page-date 26.04.22 --date 2026-04-28
autopark/.venv/bin/python autopark/scripts/build_recon_0421_format.py autopark/recon/26.04.22.md --selection autopark/data/processed/2026-04-28/storyline-selection-v3.json --feature-stocks autopark/runtime/notion/2026-04-28/feature-stock-cards.md --output autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
```

결과:

- 새 4/22 page published
  - old page id: `350468fb-878d-8131-9d8d-fc30ef5f49b4`
  - new page id: `350468fb-878d-8159-b036-f2f317bc477e`
  - url: `https://www.notion.so/26-04-22-350468fb878d8159b036f2f317bc477e`
  - blocks: 192, chunks: 2

운영 메모:

- SpaceX 카드는 원문 서류/보도 출처가 확실해지기 전까지 수치 인용을 보수적으로 다룬다.
- 다음 단계는 특징주별 Finviz 캡처 또는 Yahoo/Datawrapper 기반 일봉 이미지를 자동 생성해 카드에 실제 이미지를 붙이는 것이다.

### 2026-04-28. Finviz feature-stock chart/news capture

목표:

- 4/22 `3. 실적/특징주 분석` 카드에 Finviz 일봉 차트를 실제 이미지로 삽입한다.
- Finviz quote page 상단의 이슈 요약/최근 뉴스 헤드라인을 함께 수집해, 왜 해당 티커를 볼 만한지 찾는 출발점으로 둔다.

구현:

- `autopark/scripts/capture_finviz_feature_stocks.mjs`
  - 기본 티커: `ISRG`, `UAL`, `MSFT`, `PANW`, `AMD`, `COIN`, `CSCO`, `MRVL`, `ON`, `COHR`.
  - headed Chrome + persistent `finviz` profile로 Cloudflare/security verification을 우회한다.
  - quote page의 가장 큰 chart canvas를 crop해 `runtime/screenshots/YYYY-MM-DD/feature-stocks/finviz-<ticker>-daily.png`에 저장한다.
  - `table.news-table`에서 최근 뉴스 8개를 수집한다.
  - 상단 이슈 문장/요약성 headline을 `quote_summary`로 별도 저장한다.
- `autopark/scripts/build_feature_stock_cards.py`
  - `--finviz-enrichment` 옵션을 추가했다.
  - JSON의 `screenshot_path`, `quote_summary`, `news`를 카드에 병합한다.
  - 카드 하단에 차트 이미지를 삽입한다.

실행:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node autopark/scripts/capture_finviz_feature_stocks.mjs --date 2026-04-28 --headed --browser-channel chrome
autopark/.venv/bin/python autopark/scripts/build_feature_stock_cards.py --page-date 26.04.22 --date 2026-04-28 --finviz-enrichment autopark/data/processed/2026-04-28/finviz-feature-stocks.json
autopark/.venv/bin/python autopark/scripts/build_recon_0421_format.py autopark/recon/26.04.22.md --selection autopark/data/processed/2026-04-28/storyline-selection-v3.json --feature-stocks autopark/runtime/notion/2026-04-28/feature-stock-cards.md --output autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v3/26.04.22.md
```

결과:

- Finviz 특징주 10개 모두 캡처 성공.
- `MRVL`은 상단 이슈 문장도 수집됨.
  - `Apr 27, 12:20 PMPOET Technologies discloses that Marvell has cancelled all purchase orders tied to Celestial AI over alleged confidentiality violations.`
- 새 4/22 page published
  - old page id: `350468fb-878d-8159-b036-f2f317bc477e`
  - new page id: `350468fb-878d-81a5-a00d-ce7803dad2bc`
  - url: `https://www.notion.so/26-04-22-350468fb878d81a5a00dce7803dad2bc`
  - blocks: 202, chunks: 3

운영 메모:

- Finviz summary가 없는 티커는 최근 뉴스 헤드라인이 대신 들어간다.
- 일부 summary는 뉴스 헤드라인/검색 출발점에 가깝다. 최종 방송 소재 선정 전에는 selector 단계에서 중복과 관련성을 다시 걸러야 한다.

### 2026-04-28. 4/22 compression pass

문제:

- `자료 배치`가 원문 제목을 그대로 사용해 너무 길었다.
- `오늘의 이모저모` 카드도 원문 제목/설명/출처가 길어 실제 진행자용 큐시트 감각이 약했다.
- 시장 차트 중 10년물, WTI, 브렌트, 달러인덱스, 원/달러는 FRED 최신성이 부족했다.
- 자료 수집이 어디까지 되었는지 한눈에 보는 리스트가 없었다.

구현:

- `autopark/scripts/build_recon_0421_format.py`
  - `short_material_title`과 `SHORT_TITLE_OVERRIDES`를 추가했다.
  - `추천 스토리라인 > 자료 배치`와 `2. 오늘의 이모저모` heading은 같은 짧은 제목을 쓴다.
  - 원문 제목은 `볼 포인트 > 원문`으로만 남긴다.
  - `자료 수집` 아래에 `수집 현황` bullet list를 추가한다.
  - FRED 노출 대신 `데이터: 시장 데이터`로 표기한다.
- `autopark/scripts/build_feature_stock_cards.py`
  - `주요 내용`을 `볼 포인트`로 줄이고, `필요 자료`류 내부 메모는 제거했다.
  - Finviz 요약/뉴스는 각각 1~2개만 노출한다.
- `autopark/config/market_charts.json`
  - `us10y`, `crude-oil-wti`, `crude-oil-brent`, `dollar-index`, `usd-krw`를 Yahoo Finance 우선/FRED fallback으로 바꿨다.
  - `dollar-index` title/label은 `DXY`로 교체했다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart us10y --source yahoo_finance --range 1y --interval 1d
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart crude-oil-wti --source yahoo_finance --range 1y --interval 1d
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart crude-oil-brent --source yahoo_finance --range 1y --interval 1d
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart dollar-index --source yahoo_finance --range 1y --interval 1d
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart usd-krw --source yahoo_finance --range 1y --interval 1d
autopark/.venv/bin/python autopark/scripts/build_recon_0421_format.py autopark/recon/26.04.22.md --selection autopark/data/processed/2026-04-28/storyline-selection-v3.json --finviz-enrichment autopark/data/processed/2026-04-28/finviz-feature-stocks.json --feature-stocks autopark/runtime/notion/2026-04-28/feature-stock-cards.md --output autopark/runtime/notion/2026-04-28/0421-format-v4/26.04.22.md
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v4/26.04.22.md
```

결과:

- 새 4/22 page published
  - old page id: `350468fb-878d-8165-a451-cef7efe0c243`
  - new page id: `350468fb-878d-8108-8723-f71f0eed1777`
  - url: `https://www.notion.so/26-04-22-350468fb878d81088723f71f0eed1777`
  - blocks: 210, chunks: 3
- Notion 검산:
  - `자료 배치`가 `S&P500 강세/약세 지표`, `포지셔닝 vs 실적`, `달러/엔 고점권`, `GM 가이던스 상향` 등 짧은 제목으로 반영됨.
  - `수집 현황`이 nested bullet list로 반영됨.
  - `DXY`, `10년물 국채금리`, WTI, 브렌트, 원/달러 이미지가 새 Datawrapper export로 반영됨.

### 2026-04-28. v4 selector, visual reasoning gate, and 4/22 rebuild runner

이번 패스의 목표:

- 4/23은 건드리지 않고 4/22만 운영형 문서로 재빌드한다.
- 시장 데이터 유료/공식 소스 판단은 보류하고, 현재 Yahoo 기반 결과를 유지한다.
- 선별 모델은 개별 URL 단발 판별이 아니라 클러스터 대표 재료를 한 번에 보며 3개 스토리라인을 짜게 한다.
- 이미지 해석은 모든 이미지에 쓰지 않고, 어려운 차트 후보에만 선택적으로 쓴다.

구현:

- `autopark/scripts/select_storylines_v4.py`
  - `today-misc-clusters.json`의 클러스터를 item count와 대표 재료 품질 기준으로 줄인다.
  - 대표 재료 19개만 모델에 전달해 선별 비용과 토큰을 줄인다.
  - 결과는 `storyline-selection-v4.json/md`로 저장한다.
- `autopark/scripts/build_visual_cards.py`
  - `needs_visual_reasoning`과 `visual_reasoning_reasons`를 실제 카드에 기록한다.
  - Isabelnet 같은 특수 차트 소스, 차트/포지셔닝/실적/금리 키워드, 주변 설명 부족 여부를 신호로 쓴다.
- `autopark/scripts/caption_visual_assets.py`
  - `--only-needs-visual-reasoning` 옵션을 추가했다.
  - `visual-cards.json`에서 플래그가 선 카드만 vision model에 보낸다.
- `autopark/scripts/publish_recon_to_notion.py`
  - Markdown table을 Notion native `table` block으로 변환한다.
- `autopark/scripts/rebuild_0422_dashboard.py`
  - 4/22 특징주 카드 생성, 04.21 포맷 문서 생성, 선택 시 Notion publish까지 묶는다.
  - v4 파일이 비어 있으면 v3 선택 결과로 자동 fallback한다.

검증:

```bash
autopark/.venv/bin/python -m py_compile autopark/scripts/publish_recon_to_notion.py autopark/scripts/build_recon_0421_format.py autopark/scripts/build_feature_stock_cards.py autopark/scripts/select_storylines_v4.py autopark/scripts/build_visual_cards.py autopark/scripts/caption_visual_assets.py autopark/scripts/rebuild_0422_dashboard.py
autopark/.venv/bin/python autopark/scripts/select_storylines_v4.py --date 2026-04-28 --sample-outline autopark/runtime/notion/2026-04-28/example-0421-outline.json --selected-count 8
autopark/.venv/bin/python autopark/scripts/build_visual_cards.py --date 2026-04-28
autopark/.venv/bin/python autopark/scripts/caption_visual_assets.py --date 2026-04-28 --only-needs-visual-reasoning --dry-run
autopark/.venv/bin/python autopark/scripts/rebuild_0422_dashboard.py
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v4/26.04.22.md
autopark/.venv/bin/python autopark/scripts/inspect_notion_page.py --page-id 350468fb-878d-8117-be36-f2ab11146d11
```

결과:

- `visual-cards.json`: 이미지 카드 8개, 모두 `needs_visual_reasoning` 후보로 flag.
- vision dry-run: flag된 후보 중 6개가 caption 대상이 되는 것을 확인.
- v4 selector: 클러스터 대표 재료 19개에서 8개 자료와 3개 스토리라인 생성.
- 4/22 page published:
  - old page id: `350468fb-878d-8108-8723-f71f0eed1777`
  - new page id: `350468fb-878d-8117-be36-f2ab11146d11`
  - url: `https://www.notion.so/26-04-22-350468fb878d8117be36f2ab11146d11`
  - blocks: 202, chunks: 3
- Notion inspect 결과 `수집 현황`은 native `table` block과 7개 `table_row`로 반영됨.

운영 메모:

- 하루 수백 건 수집 시 모델은 URL을 읽지 않고, 수집기가 만든 축약 재료/클러스터만 읽는다.
- `caption_visual_assets.py --only-needs-visual-reasoning`은 비용 상한을 두기 위해 `--limit`과 함께 쓴다.
- 4/22 운영 문서는 replace publish로 관리하고, 실험 로그는 이 문서와 로컬 산출물에만 남긴다.

### 2026-04-28. Flat card metadata pass

사용자 피드백:

- `출처`, `캡처`, `작성 일자`가 모두 bullet이면 문서가 지나치게 계단식으로 보인다.
- `볼 포인트` wrapper bullet도 내용 깊이를 불필요하게 한 단계 늘린다.

구현:

- `build_recon_0421_format.py`
  - 연속된 `출처`/`캡처`/`데이터`/`작성 일자` bullet을 한 줄 metadata paragraph로 평탄화한다.
  - `2. 오늘의 이모저모` 카드에서 `볼 포인트`를 제거하고 본문을 바로 1-depth bullet로 렌더링한다.
- `build_feature_stock_cards.py`
  - 특징주 카드도 `출처: ... · 캡처: ...` metadata paragraph를 사용한다.
  - `Finviz 출발점`, `Finviz 최근 뉴스`는 nested bullet이 아니라 1-depth bullet로 표시한다.

결과:

- 새 4/22 page published:
  - old page id: `350468fb-878d-8117-be36-f2ab11146d11`
  - new page id: `350468fb-878d-81c1-9d3c-d08d6d918033`
  - url: `https://www.notion.so/26-04-22-350468fb878d81c19d3cd08d6d918033`
  - blocks: 204, chunks: 3
- Notion inspect 결과 metadata는 paragraph, 본문 포인트는 1-depth bullet로 반영됨.

### 2026-04-28. Metadata timestamp wording

사용자 피드백:

- 자동화가 모든 소스를 한 순간에 수집하지는 않으므로, 시장 지표와 캡처류는 관찰 기준 시점이 중요하다.
- `캡처`보다는 `수집 시점`, `작성 일자`보다는 `작성 시점`이 장기 운영에 맞다.
- 가능하면 일시를 쓰고, 원천 데이터에 시간이 없으면 일자만 표시한다.

구현:

- `build_recon_0421_format.py`
  - 시장/차트/캡처류 metadata를 `수집 시점`으로 출력한다.
  - 이모저모 기사/X/리서치 자료 metadata를 `작성 시점`으로 출력한다.
  - legacy label `캡처`, `작성 일자`가 들어와도 각각 `수집 시점`, `작성 시점`으로 정규화한다.
- `build_feature_stock_cards.py`
  - Finviz 차트/뉴스 출발점 카드는 `수집 시점`.
  - 실적 일정/SEC 등 문서형 자료는 `작성 시점`.

결과:

- 새 4/22 page published:
  - old page id: `350468fb-878d-818c-bbfb-f22fa7c7599a`
  - new page id: `350468fb-878d-8177-9a3d-d38ba17939f0`
  - url: `https://www.notion.so/26-04-22-350468fb878d81779a3dd38ba17939f0`
- Notion inspect 결과:
  - 시장 지표: `데이터: 시장 데이터 · 수집 시점: 26.04.28 05:00`
  - 이모저모 자료: `출처: Isabelnet · 작성 시점: 26.04.28`
  - 특징주 Finviz: `출처: Finviz · 수집 시점: 26.04.22 05:30`

### 2026-04-28. Slide refs, feature tickers, and chart 기준 wording

사용자 피드백:

- 특징주 ticker는 별도 bullet이 아니라 소제목 옆 괄호로 둔다.
- Finviz issue/news는 `Finviz 출발점`, `Finviz 최근 뉴스` 같은 wrapper label 없이 내용만 둔다.
- 시장 차트 안의 부제는 `현재`가 아니라 구체적인 `수집 기준` 시점과 최신값을 함께 둔다.
- 스토리라인의 자료 참조는 `자료 배치` bullet로 분리하지 않고, 슬라이드 구성 아래 문장형 `참고 자료`로 둔다.

구현:

- `build_feature_stock_cards.py`
  - 특징주 heading을 `회사명 (TICKER)`로 렌더링한다.
  - Finviz summary는 1-depth bullet 본문으로만 표시한다.
  - Finviz recent news wrapper bullet은 제거했다.
- `build_recon_0421_format.py`
  - `슬라이드 구성` 아래 `자료 배치` bullet을 없애고 `참고 자료: A -> B` 문장으로 바꿨다.
- `fetch_market_chart_data.py`
  - `--collected-at` 옵션을 추가했다.
  - Datawrapper subtitle/intro를 `26.04.28 05:00 수집 기준 ...` 형태로 생성한다.

실행:

```bash
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart us10y --source yahoo_finance --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart crude-oil-wti --source yahoo_finance --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart crude-oil-brent --source yahoo_finance --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart dollar-index --source yahoo_finance --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart usd-krw --source yahoo_finance --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart bitcoin --source coingecko --range 1y --interval 1d --collected-at '26.04.28 05:00'
autopark/.venv/bin/python autopark/scripts/rebuild_0422_dashboard.py
autopark/.venv/bin/python autopark/scripts/publish_recon_to_notion.py --replace-existing autopark/runtime/notion/2026-04-28/0421-format-v4/26.04.22.md
```

결과:

- Datawrapper charts republished/exported:
  - 10년물 `nofn2`
  - WTI `TYqZk`
  - 브렌트 `jZDeO`
  - DXY `aIYNm`
  - 원/달러 `tTyEQ`
  - 비트코인 `87wAG`
- 새 4/22 page published:
  - old page id: `350468fb-878d-8177-9a3d-d38ba17939f0`
  - new page id: `350468fb-878d-81ed-b997-cb0721430929`
  - url: `https://www.notion.so/26-04-22-350468fb878d81edb997cb0721430929`
- Notion inspect 결과:
  - 상단 스토리라인에 `참고 자료` 문장형 참조가 들어갔다.
  - 특징주 heading은 `인튜이티브 서지컬 (ISRG)`처럼 ticker를 옆에 둔다.
  - `Finviz 출발점`, `Finviz 최근 뉴스`, `티커:` 텍스트는 노출되지 않는다.
  - 시장 지표 metadata는 `수집 시점`, 차트 내부 부제는 `수집 기준`으로 정리됐다.

### 2026-04-28. Datawrapper title/footnote and calendar filter pass

사용자 피드백:

- 시장 차트의 최신값은 부제보다 제목에 붙이는 편이 더 잘 보인다.
- `수집 기준`은 Datawrapper 하단 각주로 보낸다.
- Notion 시장 지표 메타는 `데이터: 시장 데이터`가 아니라 실제 출처명/링크를 보여준다.
- 경제캘린더는 미국 2★ 이상, 기타 국가는 3★만 남긴다.
- 실적 캘린더는 Earnings Whispers X 이미지로 교체 가능하다.
- 특징주 섹션에서 실적 캘린더/테마 지도 같은 상위 자료와 개별 주식 종목의 위계를 나눈다.

구현:

- `fetch_market_chart_data.py`
  - Datawrapper `title`을 `지표명: 최신값` 형태로 만든다.
  - `subtitle`/`intro`는 비우고 `metadata.annotate.notes`에 `수집 기준: 26.04.28 05:00`을 쓴다.
  - Yahoo Finance/FRED/CoinGecko source URL은 가능하면 세부 quote/series/coin URL로 만든다.
- `fetch_economic_calendar.py`
  - 미국은 2★ 이상, 미국 외 국가는 3★ 이상만 통과시키는 필터를 추가했다.
  - 26.04.28 기준 경제캘린더는 4건으로 축소되어 PNG 하단 잘림은 없어졌다.
- `collect_x_timeline.mjs`
  - `fixed-earnings-calendar` 소스를 대상으로 실행해 Earnings Whispers 주간 실적 캘린더 이미지를 저장했다.
- `build_feature_stock_cards.py`
  - Earnings Whispers X 이미지와 status URL을 실적 캘린더 카드에 연결한다.
  - 개별 종목 카드는 `####`로 렌더링한다.
- `publish_recon_to_notion.py`
  - `####`를 Notion heading으로 올리지 않고 작은 bold paragraph로 변환한다.
  - inline bold annotation을 지원한다.
- `build_recon_0421_format.py`
  - 10년물, WTI, 브렌트, DXY, 원/달러의 Notion metadata를 `출처: Yahoo Finance` 링크로 바꿨다.

결과:

- Datawrapper charts republished/exported:
  - 10년물 `nofn2`: `미국 10년물 국채금리: 4.368%`
  - WTI `TYqZk`: `WTI: $100.02`
  - 브렌트 `jZDeO`: `브렌트: $104.46`
  - DXY `aIYNm`: `DXY: 98.711`
  - 원/달러 `tTyEQ`: `원/달러: 1,474.76원`
  - 비트코인 `87wAG`: `비트코인: $75,942.19`
  - 경제캘린더 `mPSRp`: 미국 2★ 이상, 기타 국가 3★
- 새 4/22 page published:
  - old page id: `350468fb-878d-81ed-b997-cb0721430929`
  - new page id: `350468fb-878d-8172-900d-c410062925d4`
  - url: `https://www.notion.so/26-04-22-350468fb878d8172900dc410062925d4`
- Visual check:
  - 10년물 PNG에서 제목 최신값, 하단 각주, Yahoo Finance source가 확인됐다.
  - 경제캘린더 PNG는 4건만 남아 하단 잘림 없이 렌더링됐다.

### 2026-04-28. Final display cleanup before next planning pass

사용자 피드백:

- 경제 일정은 별도 crop 없이 쓰되, Buykings 로고만 다른 이미지보다 작게 둔다.
- 시장 차트는 각주 없이 부제를 다시 사용한다.
- 부제 문구는 `26.04.28 05:00 기준`으로 통일한다.
- 실적/특징주 상위 카드에는 quote를 굳이 달지 않는다.
- 개별 종목 quote는 “왜 볼 종목인가”보다 전날/최근 어떤 이슈가 있었는지 중심으로 쓴다.

구현:

- `fetch_market_chart_data.py`
  - 제목은 최신값 포함을 유지한다.
  - `subtitle`/`intro`를 `26.04.28 05:00 기준`으로 바꿨다.
  - `annotate.notes`는 빈 값으로 patch해 Datawrapper의 이전 각주를 제거한다.
- `build_feature_stock_cards.py`
  - 비종목 상위 카드 quote를 생략한다.
  - 개별 종목 quote는 Finviz 뉴스/요약을 바탕으로 짧은 한국어 이슈 문장으로 교체했다.
- 경제캘린더 PNG는 `--logo-height-ratio 0.07`로 재export했다.

결과:

- 새 4/22 page published:
  - old page id: `350468fb-878d-8172-900d-c410062925d4`
  - new page id: `350468fb-878d-8114-9c64-c09e07131efb`
  - url: `https://www.notion.so/26-04-22-350468fb878d81149c64c09e07131efb`
- Visual check:
  - 10년물 PNG는 제목 최신값, `26.04.28 05:00 기준` 부제, 각주 없음 상태로 확인됐다.
  - 경제캘린더 PNG는 full export 상태에서 로고 크기만 줄어든 것을 확인했다.
