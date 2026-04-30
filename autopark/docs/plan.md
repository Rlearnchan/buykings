# Autopark Plan

기준일: 2026-04-28

## Goal

아침방송 준비에 필요한 입력을 자동으로 모아 한 화면에서 검토할 수 있게 한다.
최종 상태는 아래 흐름이다.

`시장 데이터/API 수집 -> Datawrapper 차트 제작 -> 원문/스크린샷 내부 보관 -> Wepoll 지수 결합 -> 스토리 라인 후보 3개 작성 -> Notion 적재 -> 서버 이관`

## Design Principles

- 사이트별 지식은 코드보다 매니페스트와 문서에 먼저 쌓는다.
- Datawrapper로 대체 가능한 고정 차트는 사이트 캡처보다 구조화 데이터를 우선한다.
- 캡처, 원문, 해석 메모, 생성 문안은 같은 날짜 키로 묶는다.
- 브라우저 자동화는 Playwright 기반으로 두되, 최종 산출물이 아니라 내부 증빙/장애 감지 역할로 둔다.
- Notion 적재는 API 우선, API 제약이 크면 브라우저 자동화로 폴백한다.
- Buykings 상위 runner는 orchestration만 맡고, Autopark 내부가 도메인 로직을 가진다.

## Existing Buykings Lessons

현재 Buykings에는 재사용할 만한 패턴이 있다.

- `config/buykings-morning.json`: 상위 job manifest
- `scripts/run_buykings_morning.py`: enabled job 실행과 JSON 결과 집계
- Wepoll daily flow: raw 수집, 지수 산출, Datawrapper publish, SQLite sync를 단계별로 분리
- 문서화 패턴: runbook과 architecture 문서를 먼저 만들고, 자동화를 점진적으로 붙임

Autopark도 같은 방식으로 간다. 먼저 독립 실행 가능한 job으로 만들고,
그 다음 상위 morning manifest에 붙인다.

## Proposed Stages

### 1. collect

시장 API와 구조화 추출로 고정 차트의 원천 데이터를 저장한다.

산출물:

- `data/raw/YYYY-MM-DD/<chart>-market-data.json`
- `prepared/<chart>-YYYY-MM-DD.csv`
- 수집 로그 JSON

### 2. prepare_charts

Datawrapper 입력 CSV와 chart spec을 생성하고, 기존 Buykings Datawrapper publish/export 스크립트를 호출한다.

산출물:

- `charts/<chart>-datawrapper.json`
- `exports/current/<chart>.png`

### 3. collect_screenshots_internal

경제 사이트 화면 캡처는 원본 확인, 장애 감지, 내부 시행착오 기록용으로만 보관한다.

산출물:

- `runtime/screenshots/YYYY-MM-DD/<site>.png`
- `data/raw/YYYY-MM-DD/<site>.json`

### 4. enrich

수집 원문에 Wepoll 지수, 시장 지표, 전일 대비 변화, 사용자가 준 해석 노하우를 결합한다.

산출물:

- `data/processed/YYYY-MM-DD/morning_inputs.json`

### 5. draft

방송용 스토리 라인 후보 3개를 만든다.

각 후보는 아래 구조를 가진다.

- headline
- why_today
- supporting_evidence
- chart_or_capture_refs
- caveats
- opening_script_draft

### 6. review

대시보드에서 사람이 최종 확인한다.

초기에는 정적 HTML 또는 JSON preview로 시작하고,
필요해지면 FastAPI/Streamlit/React 중 하나로 확장한다.

### 7. publish_notion

승인된 Datawrapper 차트 이미지, 원문 링크, 스토리 라인 후보를 Notion 페이지에 적재한다.

초기 구현 순서:

1. Notion API로 새 페이지/블록 생성
2. 기존 페이지의 특정 블록 갱신
3. API로 어려운 위치 조작은 Playwright 폴백 검토

### 8. ship_server

서버에서 매일 실행되도록 옮긴다.

초기에는 단일 cron/Task Scheduler job으로 충분하고,
브라우저 세션이 필요한 사이트가 많아지면 long-lived fetcher와 batch runner를 분리한다.

## Site Onboarding Template

사이트별로 사용자가 전달해줄 항목:

- site id
- URL 또는 북마크 이름
- 로그인 필요 여부
- 캡처해야 할 영역
- 스크롤/탭/필터 규칙
- 반드시 읽어야 하는 숫자/문장
- 해석 노하우
- 방송에서 쓸 때의 주의점

이 정보는 `config/autopark.json`의 `sources`에 하나씩 추가한다.

## First Milestones

1. 프로젝트 골격과 venv 생성
2. 매니페스트 기반 dry-run 러너 준비
3. 고정 시장 차트 계획을 `config/market_charts.json`에 등록
4. Yahoo/FRED 등 구조화 데이터 fetch PoC 작성
5. Datawrapper CSV/spec 생성과 publish/export PoC
6. Playwright 캡처는 내부 증빙 파이프라인으로 유지
7. Wepoll 산출물 read-only 결합
8. 스토리 후보 JSON 생성
9. Notion 적재 PoC
10. Buykings morning runner에 enabled job으로 편입

## Reconstruction Seeds

방송 준비자가 당일 PPT를 만들기 전에 참고했을 법한 Notion-ready 역구성 초안:

- `recon/26.04.22.md`
- `recon/26.04.23.md`

이 두 파일은 자동화가 채워야 할 항목을 드러내기 위한 1차 작업물이다.
이미지/원문 URL은 아직 완전히 채워진 상태가 아니며, 날짜별로 필요한
시장 차트, 후보 출처, 병목을 적었다. PPT 내용은 결과 검증용 참고자료이지
선정 근거로 문서에 쓰지 않는다.

현재 확인된 추가 수집 병목:

- 러셀 2000 히트맵 URL과 캡처 규칙
- Investing 경제캘린더의 당일/주간 지표 캡처 규칙
- Bloomberg/Reuters/CNBC/X 속보를 `today_misc` 후보로 모으는 방식
- FactSet/Fidelity/Isabelnet/Advisor Perspectives 같은 고급 차트 소스의 접근 방식
- Notion write 권한 또는 Notion API 토큰

## Notion Publishing

`scripts/publish_recon_to_notion.py`는 로컬 Markdown 초안을 Notion 페이지로 만든다.

필요 환경:

- repo root의 `.env`
- `NOTION_API_KEY`
- `config/autopark.json`의 `integrations.notion.dashboard_parent_page_id`

게시된 페이지:

- `26.04.22`: https://www.notion.so/26-04-22-350468fb878d81149c64c09e07131efb
- `26.04.23`: https://www.notion.so/26-04-23-350468fb878d81b7bad1c66b5d61439a

운영 규칙:

- 실제 Notion 반영 대상은 현재 `26.04.22`, `26.04.23` 역구성 문서다.
- 구현 중 생기는 시행착오, 캡처 상태, batch 결과, 테스트 날짜 산출물은 내부 문서와 로컬 산출물에만 저장한다.
- 테스트 날짜 페이지를 실수로 게시한 경우 `--archive-existing-only`로 같은 제목 페이지를 archive 처리한다.
- 2026-04-28 기준 `26.04.22`, `26.04.23`은 Datawrapper 기반 10년물/WTI/브렌트/달러 지수/원달러/비트코인 이미지를 `1. 시장은 지금` 섹션에 배치한 버전으로 교체 게시했다.
- `26.04.22`는 후속 개선으로 짧은 자료명, Notion table 기반 수집 현황, Yahoo Finance 우선 시장 차트(DXY 포함), Finviz 특징주 일봉/뉴스, v4 클러스터 선별 결과, 평평한 메타/본문 카드 포맷, 짧은 출처명 링크를 반영했다.
- 2026-04-28 기준 `26.04.22`는 특징주 heading 옆 ticker 표기, Finviz 최근 뉴스 wrapper 제거, 시장 차트의 `수집 기준` 부제, 스토리라인 `참고 자료` 문장형 배치를 반영한 버전으로 교체했다.
- 시장 Datawrapper 차트는 제목에 최신값을 붙이고, 부제에는 `26.04.28 05:00 기준`처럼 기준 시각만 둔다. Notion 메타데이터는 `출처: Yahoo Finance`처럼 실제 데이터 출처 링크를 표시한다.
- Trading Economics 공개 HTML을 파싱한 경제캘린더 table도 Datawrapper `mPSRp`로 제작해 두 문서의 `경제지표` 위치에 삽입했다.
- 2026-04-28 기준 append가 누적된 기존 `26.04.22`, `26.04.23` 페이지를 archive하고, `2. 오늘의 이모저모` 섹션을 선별·스토리라인 v2로 교체한 clean recon 페이지를 새로 게시했다.

주의:

- 현재 퍼블리셔는 Markdown을 Notion 기본 블록으로 변환하고, 로컬 이미지 업로드와 기본 중첩 bullet을 처리한다.
- `--replace-existing`을 쓰면 같은 parent 아래 같은 제목의 기존 페이지를 먼저 archive 처리한 뒤 새 페이지를 만든다.
- `--replace-existing` 없이 재실행하면 새 페이지가 추가된다.
- `--archive-existing-only`를 쓰면 같은 제목의 기존 페이지를 archive 처리하고 새 페이지를 만들지 않는다.
- 2026-04-28 기준 4/22 전용 재빌드는 `autopark/scripts/rebuild_0422_dashboard.py`로 묶었다. 기본은 로컬 Markdown 생성이고, `--publish`를 붙이면 Notion까지 replace publish한다.

## Capture PoC

2026-04-27에 `scripts/capture_source.mjs`로 첫 source 단위 캡처를 확인했다.
자세한 상태표는 `docs/capture-status.md`에 둔다.
`scripts/capture_batch.mjs`는 `known_capture_issue`가 없는 source만 묶어 실행한다.
`scripts/build_morning_inputs.mjs`는 raw metadata를 processed JSON과 내부 검토용 Markdown으로 묶는다.

역할 변경:

- `1. 시장은 지금`, `3. 특징주 분석`의 고정 차트는 Datawrapper 산출물을 우선한다.
- Finviz/CNBC/CNN/Investing 캡처는 내부 증빙과 원본 화면 변화 감지용으로 유지한다.
- 로그인이나 보안 검증이 필요한 사이트는 headed Chrome persistent profile을 쓴다.

현재 결론:

- Finviz는 persistent profile로 캡처 가능하지만, 최종 차트 품질은 Datawrapper 전환이 낫다.
- CNBC 10년물과 CNN 공포탐욕은 캡처/수치 추출이 가능하나, 장기적으로는 자체 차트/게이지로 대체한다.
- Investing 차트 iframe은 profile을 써도 비어 있을 수 있어 캡처 최종 산출물로 쓰지 않는다.

## Open Questions

- 대시보드는 로컬 검토용이면 충분한가, 서버에서 웹으로 열어야 하는가?
- Notion에는 승인된 역구성 날짜만 `아침방송 준비 대시보드` 하위에 만든다.
- 스토리 라인 초안은 OpenAI API를 쓸 것인가, 로컬 모델/수동 템플릿부터 시작할 것인가?
- 서버 이관 대상은 Windows PC인가, Linux/Docker 서버인가?

## Current Status

2026-04-28 현재 Autopark는 아래까지 동작한다.

- `autopark/` 프로젝트 골격, venv, 실행 스크립트, 문서/산출물 디렉터리 구성 완료
- 4/22, 4/23 역구성 Markdown 작성 및 Notion replace publish 가능
- 로컬 이미지 업로드를 포함한 Notion page publishing PoC 완료
- 고정 시장 차트는 Datawrapper PNG 산출물로 전환
  - 10년물: FRED `DGS10`, chart `nofn2`
  - WTI: FRED `DCOILWTICO`, chart `TYqZk`
  - 브렌트: FRED `DCOILBRENTEU`, chart `jZDeO`
  - 달러 지수: FRED `DTWEXBGS`, chart `aIYNm`
  - 원/달러: FRED `DEXKOUS`, chart `tTyEQ`
  - 비트코인: CoinGecko `bitcoin`, chart `87wAG`
- Trading Economics 공개 캘린더 HTML 파싱 PoC 완료
  - 중요도는 `calendar-date-1/2/3` 클래스로 추출
  - HTML 기본 시간은 UTC로 보고 KST 변환
  - Datawrapper table chart `mPSRp`로 제작
  - 최종 table 컬럼은 `시각 / 중요도 / 국가 / 이벤트 / 예상`
- Finviz, CNN Fear & Greed 등 스크린샷 파이프라인은 내부 증빙용으로 유지
- Investing 차트 iframe은 headless/profile에서도 빈 화면이 날 수 있어 고정 차트 원천으로 쓰지 않기로 결정

## Next Candidates

우선순위가 높은 다음 작업 후보:

1. `2. 오늘의 이모저모` 자동화를 먼저 구축한다.
   - 자세한 계획: `docs/today-misc-plan.md`
   - `sources.xlsx`와 bookmark HTML을 `config/today_misc_sources.json`으로 정규화
   - 밤새 미국 증시 관련 이슈 후보를 수집/요약/중복 제거
   - 후보를 묶어 스토리라인 가안 3개를 작성
2. `run_autopark.py` 또는 새 daily runner에서 시장 차트, 경제캘린더, 이모저모 후보 생성을 한 번에 실행
3. 경제캘린더 국가/중요도/날짜 범위를 설정 파일로 분리하고, 당일 아침 기준으로 자동 생성
4. 4/22, 4/23 문서에 들어간 Datawrapper 이미지 배치 규칙을 템플릿화
5. 특징주 분석용 ticker table과 가격 차트 생성
6. Wepoll 지수 산출물 read-only 결합
7. Notion 페이지를 매번 새로 만드는 방식에서 특정 섹션/블록 갱신 방식으로 개선
8. 서버 이관 전 `autopark/docs/runbook.md` 작성
