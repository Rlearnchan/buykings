# Autopark Operating Runbook

이 문서는 매일 아침 Autopark를 어떻게 돌리고, Notion을 어떻게 검토하며, 실제 PPT/스크립트가 나온 뒤 어떤 지식을 업데이트할지 정리한다.

## Daily Flow

운영 모드는 `projects/autopark/config/broadcast_calendar.json`이 결정한다. 일반 방송일은 `daily_broadcast`, 휴일/비방송일은 `no_broadcast`, 월요일처럼 주말 누적분을 반영해야 하는 날은 `monday_catchup`으로 둔다.

- `daily_broadcast`: 당일 수집, 품질 게이트 통과 시 Notion 게시, 방송 후 회고 실행
- `no_broadcast`: 방송 회고는 정상 스킵하되, 현재 운영 검증 단계에서는 품질 게이트 통과 시 월요일 준비용 Notion 문서를 게시
- `monday_catchup`: 금요일 오전 방송 이후 주말까지 약 72시간 lookback으로 넓게 수집

Codex 자동화는 매일 05:05에 아침 대시보드 runner를 깨우고, 매일 10:30에 방송 후 회고 runner를 깨운다. 둘 다 먼저 방송 캘린더를 확인하므로 0503 같은 비방송일은 회고가 실패가 아니라 `skipped_expected_no_broadcast`로 끝나는 것이 정상이다.

### 1. 05:00 Preflight

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

### 2. 05:05-05:15 Collection

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

### 3. 05:15-05:22 Selection

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

### 4. 05:22-05:27 Notion Draft

고정 레이아웃:

1. `최종 수정 일시`
2. `뉴스/X 수집 구간`
3. `시장 데이터 기준`
4. 오늘의 핵심 질문
5. 추천 스토리라인 3-5개
6. 자료 수집
7. 시장은 지금
8. FedWatch 금리 확률, 해당 자료가 있으면 단기/장기 표로 분리
9. 오늘의 이모저모
10. 실적/특징주
11. 단신/환기, 해당일만

추천 스토리라인 규칙:

- 3-5개는 서로 다른 꼭지여야 한다.
- 강한 후보가 3개뿐이면 3개만 둔다.
- 추천도는 별 3개 만점으로 표시한다.
- 하나의 이슈를 1, 2, 3으로 쪼개지 않는다.
- 각 꼭지는 아래 자료 카드 제목을 코드 텍스트로 정확히 인용한다.
- 제목은 방송 꼭지처럼 짧게 쓴다.
- “자료를 읽어보라”가 아니라 “이 자료로 이렇게 말할 수 있다”가 보여야 한다.
- 내부 점수, 클러스터, 출처 수 로직은 본문에 노출하지 않는다.

### 5. 05:27-05:30 Self Review

발행 전 체크:

- 상단 thesis가 실제 수집 자료와 맞는가?
- 오늘의 대립축이 보이는가?
- 이모저모가 5-6개를 넘지 않는가?
- 실적 시즌이면 Wall St Engine/Finviz/Yahoo 숫자 확인이 들어갔는가?
- Fed 이벤트가 있으면 Fed package가 있는가?
- 단신/환기 소재가 메인 story와 섞이지 않았는가?
- 같은 자료가 메인과 보강 후보에 중복되지 않았는가?
- 이미지/차트 제목과 수집 시점이 정확한가?

### 6. 05:30 Publish

원칙:

- 기존 같은 날짜 페이지가 있으면 archive 후 replace한다.
- Notion에는 실험 로그를 과하게 싣지 않는다.
- 내부 로그와 장부는 runtime/docs에 남긴다.
- 발행 후 block count와 이미지 실패 여부만 확인한다.
- 07:20 방송 시작을 기준으로 진행자가 자료를 만들 시간을 확보하려면 05:30에는 대시보드가 완성돼야 한다.

### 7. 09:30-당일 오후 Post-Broadcast Retrospective

위폴 라이브 다시보기의 한국어 자동 자막이 뜨면 초반 진행자 구간만 수집한다. 기본 창은 40분이며, 이후 버디버디/게스트 구간은 자동 회고 대상에서 제외한다.

명령:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_broadcast_retrospective.py --date YYYY-MM-DD --attempts 6 --sleep-minutes 60
```

회고 산출물:

- `runtime/broadcast/YYYY-MM-DD/wepoll-transcript.json`
- `runtime/broadcast/YYYY-MM-DD/host-segment.md`
- `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.md`
- `runtime/broadcast/YYYY-MM-DD/retrospective-feedback.md`

`retrospective-feedback.md`는 다음날 `build_editorial_brief.py`가 우선 참고한다. 이 파일은 시장 사실 소스가 아니라 편집 선호와 형식 피드백이다.

## Review After Actual PPT Arrives

실제 PPT와 스크립트가 오면 같은 날 리뷰 문서를 만든다.

파일명:

- `projects/autopark/docs/MMDD-live-experiment-review.md`

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

- Fed/FOMC package 생성기 유지보수
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

## Current Lessons From 0502

- LLM 편집장 단계는 반복적인 규칙 기반 스토리라인을 줄이는 데 효과가 있다.
- 추천 스토리라인은 5개를 채우는 것보다 3개 강선별이 더 낫다.
- FedWatch는 단일 긴 표보다 단기/장기 두 표가 방송 화면에서 읽기 쉽다.
- FedWatch 히트맵은 파랑-빨강보다 `0=흰색`, 고확률=코랄 단일 강조가 낫다.
- Datawrapper table heatmap은 컬럼별 `heatmap: {"enabled": true}`가 필요하다.
- 회의일은 `26.06.17`처럼 짧게 쓰되, Datawrapper 정렬을 위해 CSV에는 `@@YYYYMMDD` suffix를 둔다.

## Next Thread Bootstrap

새 스레드에서 이어갈 때 먼저 읽을 문서:

1. `projects/autopark/docs/autopark-operating-runbook.md`
2. `projects/autopark/docs/source-playbook.md`
3. 해당 전일 리뷰 문서, 예: `projects/autopark/docs/0430-live-experiment-review.md`

시작 문장 예시:

> Autopark 0431 대시보드를 만들자. 운영 절차는 `projects/autopark/docs/autopark-operating-runbook.md`, 소스별 역할은 `projects/autopark/docs/source-playbook.md`, 전일 비교 교훈은 `projects/autopark/docs/0430-live-experiment-review.md`를 기준으로 해줘.
