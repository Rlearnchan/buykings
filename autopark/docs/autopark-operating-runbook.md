# Autopark Operating Runbook

이 문서는 매일 아침 Autopark를 어떻게 돌리고, Notion을 어떻게 검토하며, 실제 PPT/스크립트가 나온 뒤 어떤 지식을 업데이트할지 정리한다.

## Daily Flow

### 1. 06:00 Preflight

확인할 것:

- `.env` 키: Notion, Datawrapper, OpenAI, 기타 API
- Chrome/Playwright profile 상태: Finviz, X, 로그인 필요한 사이트
- 전일 산출물 잔존 여부
- 오늘 날짜 폴더 생성 여부
- 로그 파일 시작

기록할 시간:

- preflight 시작/종료
- 뉴스/X 수집 시작/종료
- 시장 데이터 수집 기준
- Notion Markdown 생성 시각
- Notion 발행 시각

### 2. 06:00-06:15 Collection

고정 수집:

- Batch A 뉴스: Reuters/Bloomberg/CNBC/Yahoo/TradingView 계열
- Batch B 특수/리서치: IsabelNet, FactSet, Bespoke, Advisor Perspectives 등
- X timeline: Wall St Engine, Kobeissi, IsabelNet, Reuters, Bloomberg, CNBC, Charlie Bilello, Liz Ann Sonders 등
- Finviz: 주요 지수, S&P500 heatmap, Russell 2000 heatmap, 특징주 일봉/hot news
- 시장 데이터: US10Y, WTI, Brent, DXY, USD/KRW, BTC
- 경제 일정: 미국 2스타 이상, 글로벌 3스타
- Earnings Whispers: 주간 실적 캘린더

조건부 수집:

- FOMC/Fed 날: FedWatch, Polymarket, FOMC statement/Powell recap
- 빅테크 실적 날: Wall St Engine posts/images 확대, after-hours movers
- 지정학/정책 이벤트 날: Polymarket trending market, Reuters/Bloomberg/CNBC 단신

### 3. 06:15-06:25 Selection

먼저 오늘의 대립축을 한 문장으로 쓴다.

좋은 예:

- `성장 vs 금리/유가`
- `AI CAPEX vs 비용 부담`
- `실적 숫자 vs 높아진 기대`
- `Fed 완화 기대 vs 인플레 재상승`

나쁜 예:

- `오늘도 AI가 중요하다`
- `유가가 올랐다`
- `좋은 뉴스가 많다`

후보는 다음 섹션 중 하나에 반드시 배치한다.

- 시장 고정 루틴
- Fed/FOMC package
- 오늘의 이모저모
- 실적/특징주
- 단신/환기
- 하단 보강 후보

### 4. 06:25-06:35 Notion Draft

고정 레이아웃:

1. `최종 수정 일시`
2. `뉴스/X 수집 구간`
3. `시장 데이터 기준`
4. 주요 뉴스 요약
5. 추천 스토리라인 3개
6. 자료 수집
7. 시장은 지금
8. Fed/FOMC package, 해당일만
9. 오늘의 이모저모
10. 실적/특징주
11. 단신/환기, 해당일만

추천 스토리라인 규칙:

- 3개는 서로 다른 꼭지여야 한다.
- 하나의 이슈를 1, 2, 3으로 쪼개지 않는다.
- 각 꼭지는 아래 자료 카드 제목을 코드 텍스트로 정확히 인용한다.
- 제목은 방송 꼭지처럼 짧게 쓴다.
- “자료를 읽어보라”가 아니라 “이 자료로 이렇게 말할 수 있다”가 보여야 한다.

### 5. 06:35-06:45 Self Review

발행 전 체크:

- 상단 thesis가 실제 수집 자료와 맞는가?
- 오늘의 대립축이 보이는가?
- 이모저모가 5-6개를 넘지 않는가?
- 실적 시즌이면 Wall St Engine/Finviz/Yahoo 숫자 확인이 들어갔는가?
- Fed 이벤트가 있으면 Fed package가 있는가?
- 단신/환기 소재가 메인 story와 섞이지 않았는가?
- 같은 자료가 메인과 보강 후보에 중복되지 않았는가?
- 이미지/차트 제목과 수집 시점이 정확한가?

### 6. 06:45 Publish

원칙:

- 기존 같은 날짜 페이지가 있으면 archive 후 replace한다.
- Notion에는 실험 로그를 과하게 싣지 않는다.
- 내부 로그와 장부는 runtime/docs에 남긴다.
- 발행 후 block count와 이미지 실패 여부만 확인한다.

## Review After Actual PPT Arrives

실제 PPT와 스크립트가 오면 같은 날 리뷰 문서를 만든다.

파일명:

- `autopark/docs/MMDD-live-experiment-review.md`

리뷰 구조:

- Executive Takeaways
- Actual PPT Narrative
- Transcript-Based Thesis
- Slide-by-Slide Comparison
- Hit / Low-Ranked Hit / Miss / False Positive
- Why The Host Selected These Stories
- Pipeline Improvements

평가 기준:

- `Hit`: Notion에 있고 실제 PPT 역할과도 맞음
- `Low-ranked hit`: 후보 또는 하단에는 있었지만, 실제 중요도보다 낮게 배치됨
- `Miss`: 수집/선별/배치 모두 실패
- `False positive`: Notion에서 과하게 밀었지만 실제 PPT에 없거나 흐름과 멀었음
- `Excluded`: 개인 브랜딩, 버디버디, 진행자 재량 코너 등 자동화 대상 아님

## Current Lessons From 0429-0430

### 0429

- 실적 캘린더는 단순 이미지가 아니라 ticker drilldown의 출발점이다.
- 실제 진행자는 “큰 테마를 증명하는 종목”을 고른다.
- 단신/환기 소재는 별도 슬롯이 없으면 탈락한다.
- 스토리라인 3개는 하나의 3막이 아니라 독립 꼭지 후보여야 한다.

### 0430

- FOMC 날에는 경제 일정 표보다 Fed package가 중요하다.
- 유가/금리 같은 macro pressure는 단독 story보다 성장주/실적과의 긴장으로 써야 한다.
- Wall St Engine은 빅테크 실적 숫자 브리핑에 매우 중요하다.
- Polymarket은 금리인하 베팅처럼 “시장이 확률로 보는 이벤트” 캡처에 유용하다.
- 실적 시즌의 좋은 카드에는 EPS/매출/핵심 사업 성장률/AI CAPEX/RPO/guidance/after-hours 반응이 있어야 한다.

## Development Backlog

### P0

- Fed/FOMC package 생성기
- Wall St Engine earnings collector 강화
- Big Tech earnings card builder
- after-hours movers + Finviz/Yahoo 차트 연결
- Notion compact mode: 이모저모 5-6개, 특징주 5개 기본

### P1

- Polymarket capture source
- FOMC statement diff
- 진행자 watchlist ticker memory
- 단신/환기 candidate slot
- source scorecard 5거래일 누적

### P2

- 지수 일봉/주봉 차트 보강
- IR release/earnings release 교차검증
- 구독/로그인 소스 Chrome profile 자동화
- PPT hit-rate 기반 선별 모델 개선

## Next Thread Bootstrap

새 스레드에서 이어갈 때 먼저 읽을 문서:

1. `autopark/docs/autopark-operating-runbook.md`
2. `autopark/docs/source-playbook.md`
3. 해당 전일 리뷰 문서, 예: `autopark/docs/0430-live-experiment-review.md`

시작 문장 예시:

> Autopark 0431 대시보드를 만들자. 운영 절차는 `autopark/docs/autopark-operating-runbook.md`, 소스별 역할은 `autopark/docs/source-playbook.md`, 전일 비교 교훈은 `autopark/docs/0430-live-experiment-review.md`를 기준으로 해줘.
