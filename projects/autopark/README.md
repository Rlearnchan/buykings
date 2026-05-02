# Autopark

Autopark는 Buykings 아침방송 준비 자동화를 위한 서브 프로젝트다.

매일 아침 확인해야 하는 시장 데이터, 뉴스/X 후보, 시각 자료, 실적/특징주, FedWatch 확률표를 모아
방송용 Notion 대시보드를 만들고, 발행 뒤 실제 위폴 라이브 방송 스크립트와 비교해 다음날 편집장 단계에
피드백을 넘기는 폐루프형 파이프라인이다.

## Current Scope

현재 운영 범위는 다음과 같다.

- 고정 시장 차트와 경제 일정은 API/구조화 데이터에서 Datawrapper PNG로 생성한다.
- Finviz, X, CME FedWatch 등 사이트 캡처는 내부 증빙과 방송 자료로 날짜별 보관한다.
- `market-radar.json` 이후 OpenAI API 기반 `editorial-brief.json`을 생성해 추천 스토리라인을 강선별한다.
- Notion 상단은 `오늘의 핵심 질문 -> 추천 스토리라인 -> 자료 수집` 순서로 렌더링한다.
- FedWatch 조건부 금리확률은 단기/장기 Datawrapper 표로 나누어 방송 화면에서 읽기 쉽게 만든다.
- 발행 뒤 위폴 유튜브 라이브 자동 자막을 수집해 실제 방송과 대시보드를 비교하는 회고록을 만든다.

## Quick Start

Windows/local runner 기준:

```powershell
cd C:\Users\User1\Documents\code\buykings
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_live_dashboard_all_in_one.py --date 2026-05-02
```

게시 없이 리허설하려면:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_live_dashboard_all_in_one.py --date 2026-05-02 --skip-publish
```

방송 이후 회고 루틴:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_broadcast_retrospective.py --date 2026-05-02 --attempts 6 --sleep-minutes 60
```

Legacy/manual commands:

```bash
cd /Users/bae/Documents/code/buykings
projects/autopark/.venv/bin/python projects/autopark/scripts/run_autopark.py --list
projects/autopark/.venv/bin/python projects/autopark/scripts/run_autopark.py --dry-run
```

List and prepare Datawrapper chart inputs:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/prepare_datawrapper_inputs.py --list
projects/autopark/.venv/bin/python projects/autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart us10y
projects/autopark/.venv/bin/python scripts/datawrapper_publish.py --dry-run projects/autopark/charts/us10y-datawrapper.json
```

Fetch the public Trading Economics calendar HTML and keep only major events:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/fetch_economic_calendar.py --date 2026-04-28
projects/autopark/.venv/bin/python projects/autopark/scripts/fetch_economic_calendar.py --date 2026-04-28 --min-importance 3
set -a; source .env; python3 scripts/datawrapper_publish.py projects/autopark/charts/economic-calendar-datawrapper.json
set -a; source .env; python3 scripts/datawrapper_export_png.py mPSRp projects/autopark/exports/current/economic-calendar.png --width 600 --scale 2 --brand-logo
```

Import source candidates for `2. 오늘의 이모저모`:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/import_today_misc_sources.py
projects/autopark/.venv/bin/python projects/autopark/scripts/collect_today_misc.py --date 2026-04-28
```

Run a pre-PPT live experiment pack:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/collect_today_misc.py --date 2026-04-29 --run-name today-misc-batch-a --overall-limit 80 --limit-per-source 15 --lookback-hours 24
projects/autopark/.venv/bin/python projects/autopark/scripts/collect_today_misc.py --date 2026-04-29 --batch-b-default --run-name today-misc-batch-b --overall-limit 80 --limit-per-source 12 --lookback-hours 36
projects/autopark/.venv/bin/python projects/autopark/scripts/cluster_today_misc.py --date 2026-04-29 --limit-news 80 --limit-x 60 --limit-visuals 40
projects/autopark/.venv/bin/python projects/autopark/scripts/select_storylines_v4.py --date 2026-04-29 --selected-count 8 --max-candidates 24
projects/autopark/.venv/bin/python projects/autopark/scripts/build_live_experiment_pack.py --date 2026-04-29
```

The freeze-ready review files are written to
`projects/autopark/data/processed/YYYY-MM-DD/live-experiment-pack.json` and
`projects/autopark/runtime/notion/YYYY-MM-DD/live-experiment-pack.md`.

## Daily Pipeline

`run_live_dashboard_all_in_one.py`의 핵심 순서는 아래와 같다.

실행 전 `config/broadcast_calendar.json`을 읽어 운영 모드를 정한다. `no_broadcast`인 날은 방송 회고를 스킵하되, 현재 운영 검증 단계에서는 품질 게이트 통과 시 월요일 준비용 Notion 문서도 게시한다. `monday_catchup`인 날은 주말 누적 이슈를 반영하기 위해 뉴스/X 수집 lookback을 72시간으로 넓힌다.

1. 뉴스/X/시각 자료/실적 캘린더/Finviz/FedWatch 소스를 수집한다.
2. 시장 차트, 경제 일정, FedWatch 단기/장기 표를 Datawrapper로 발행하고 PNG를 export한다.
3. `build_market_radar.py`가 수집 후보를 점수화하고 묶는다.
4. `build_editorial_brief.py`가 OpenAI Responses API로 3-5개 방송 글감을 강선별한다.
5. `build_live_notion_dashboard.py`가 Notion Markdown을 만든다.
6. `review_dashboard_quality.py`가 섹션, 추천도, 근거, 내부 로직 문장 노출 여부를 검사한다.
7. 품질 gate가 pass이면 `publish_recon_to_notion.py --replace-existing`으로 날짜 페이지를 교체 게시한다.
8. `post-publish-review.*`와 실행 로그를 남긴다.

API 키가 없거나 LLM 응답이 invalid JSON이면 `editorial-brief.json`은 기존 `market-radar.json` 기반 fallback으로 생성되고, 전체 파이프라인은 계속 진행한다.

## Editorial Brief

`build_editorial_brief.py`는 `market-radar.json`, `finviz-feature-stocks.json`, `visual-cards.json`, 최근 7일 `editorial-brief.json`, 최근 방송 회고 피드백을 입력으로 사용한다.

출력 파일:

- `projects/autopark/data/processed/YYYY-MM-DD/editorial-brief.json`

핵심 필드:

- `daily_thesis`: 오늘의 핵심 질문
- `editorial_summary`: 방송 전체 흐름
- `storylines[]`: 3-5개 추천 글감
- `recommendation_stars`: 1-3 별점
- `hook`, `why_now`, `core_argument`, `talk_track`, `counterpoint`
- `evidence_to_use`, `evidence_to_drop`

편집 정책은 “강하게 선별”이다. 좋은 후보가 3개뿐이면 3개만 쓰고, 약한 후보는 보조 또는 버림으로 분리한다.

## FedWatch Datawrapper

FedWatch 조건부 금리확률은 한 표가 길어지는 것을 피하기 위해 단기/장기 두 표로 나눈다.

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\prepare_fedwatch_datawrapper_splits.py --date 2026-05-02
```

산출물:

- `prepared/fedwatch-conditional-probabilities-short-term-YYYY-MM-DD.csv`
- `prepared/fedwatch-conditional-probabilities-long-term-YYYY-MM-DD.csv`
- `charts/fedwatch-conditional-probabilities-short-term-datawrapper.json`
- `charts/fedwatch-conditional-probabilities-long-term-datawrapper.json`
- `exports/current/fedwatch-conditional-probabilities-short-term.png`
- `exports/current/fedwatch-conditional-probabilities-long-term.png`

히트맵은 `0 = 흰색`, `100 = 부드러운 코랄`의 연속형 프로필을 사용한다. 날짜 컬럼은 `26.06.17@@20260617` 같은 Datawrapper sort suffix를 붙여 짧게 보이면서 정렬이 깨지지 않게 한다.

## Post-Broadcast Retrospective

위폴 채널의 라이브 다시보기 자동 자막이 생성되면 `run_broadcast_retrospective.py`가 초반 진행자 구간을 수집하고, Notion 대시보드와 비교해 회고록을 만든다.

산출물:

- `runtime/broadcast/YYYY-MM-DD/wepoll-transcript.json`
- `runtime/broadcast/YYYY-MM-DD/host-segment.md`
- `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.md`
- `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.json`
- `runtime/broadcast/YYYY-MM-DD/retrospective-feedback.md`

다음날 `build_editorial_brief.py`는 원문 자막보다 `retrospective-feedback.md`를 우선 참고한다. 회고는 새로운 시장 사실로 쓰지 않고, 실제 진행자가 어떤 형식과 소재를 사용했는지 배우는 피드백으로만 사용한다.

Screenshots are still useful, but now as internal evidence and site-change diagnostics.

Capture one source:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source finviz-sp500-heatmap
```

Bootstrap a site profile for sources that require a normal browser session:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source finviz-sp500-heatmap --bootstrap --browser-channel chrome --bootstrap-wait-ms 180000
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source investing-wti --bootstrap --browser-channel chrome --bootstrap-wait-ms 180000
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source earnings-whispers-x --bootstrap --browser-channel chrome --bootstrap-wait-ms 300000
```

After the first manual login/security check, reuse those profiles:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source finviz-sp500-heatmap --use-auth-profiles --headed --browser-channel chrome
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_batch.mjs --section market_now --include-known-issues --use-auth-profiles --headed --browser-channel chrome
```

Profiles live under `projects/autopark/runtime/profiles/` and are git-ignored because
they may contain login cookies and browser session state.

Capture all currently safe sources in a section:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_batch.mjs --section market_now --dry-run
```

Summarize captured metadata:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/summarize_capture.mjs --date 2026-04-27
```

Build processed morning inputs and a Notion-ready page:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/build_morning_inputs.mjs --date 2026-04-27
```

Publish reconstruction drafts to Notion:

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/publish_recon_to_notion.py --dry-run projects/autopark/recon/26.04.22.md
projects/autopark/.venv/bin/python projects/autopark/scripts/publish_recon_to_notion.py projects/autopark/recon/26.04.22.md
projects/autopark/.venv/bin/python projects/autopark/scripts/publish_recon_to_notion.py --replace-existing projects/autopark/recon/26.04.22.md
projects/autopark/.venv/bin/python projects/autopark/scripts/publish_recon_to_notion.py --archive-existing-only projects/autopark/runtime/notion/2026-04-27/26.04.27.md
```

Notion publishing is currently limited to reconstruction targets such as `26.04.22`
and `26.04.23`. Operational trial runs, including `2026-04-27`, stay in local
internal docs and generated files unless explicitly promoted.

## Layout

- `config/autopark.json`: 단계와 사이트별 수집 항목 매니페스트
- `config/market_charts.json`: Datawrapper로 제작할 고정 시장/특징주 차트 계획
- `docs/plan.md`: 구현 로드맵과 설계 메모
- `docs/datawrapper-transition.md`: 캡처 중심에서 데이터/Datawrapper 중심으로 바꾼 운영 결정
- `docs/0429-live-experiment-plan.md`: 실제 PPT 공개 전 30분 리허설 운영 계획
- `scripts/run_autopark.py`: 초기 파이프라인 러너
- `scripts/prepare_datawrapper_inputs.py`: Datawrapper CSV/spec 자리표시자와 계획 출력
- `scripts/fetch_market_chart_data.py`: Yahoo Finance 기반 Datawrapper 입력 CSV/spec 생성 PoC
- `scripts/fetch_economic_calendar.py`: Trading Economics 공개 캘린더 HTML을 파싱해 주요 경제 일정 JSON/Markdown 생성
- `scripts/import_today_misc_sources.py`: bookmark HTML과 sources.xlsx에서 이모저모 source registry 초안 생성
- `scripts/collect_today_misc.py`: 이모저모 source registry에서 headline 후보를 수집하고 review Markdown 생성
- `scripts/capture_source.mjs`: 매니페스트 source 한 개를 브라우저로 캡처
- `scripts/capture_batch.mjs`: known issue가 없는 source를 묶어 순차 캡처
- `scripts/summarize_capture.mjs`: 캡처 metadata를 방송 준비용 한 줄 요약으로 정리
- `scripts/build_morning_inputs.mjs`: raw metadata를 processed JSON과 Notion용 Markdown으로 변환
- `scripts/build_market_radar.py`: 수집 후보를 방송용 후보 장부로 점수화
- `scripts/build_editorial_brief.py`: LLM 편집장 단계, 추천 스토리라인 3-5개 생성
- `scripts/prepare_fedwatch_datawrapper_splits.py`: FedWatch 확률표를 단기/장기 Datawrapper 입력으로 분할
- `scripts/build_live_notion_dashboard.py`: 일별 Notion 대시보드 Markdown 생성
- `scripts/review_dashboard_quality.py`: 발행 전 품질 gate
- `scripts/run_live_dashboard_all_in_one.py`: 수집부터 Notion 게시까지 일괄 실행
- `scripts/fetch_wepoll_transcript.py`: 위폴 유튜브 라이브 다시보기 한국어 자막 수집
- `scripts/build_broadcast_retrospective.py`: 실제 방송 스크립트와 대시보드 비교 회고
- `scripts/run_broadcast_retrospective.py`: 방송 후 자막 수집/회고 일괄 실행
- `scripts/build_live_experiment_pack.py`: 사전 선별 결과와 탈락 후보를 freeze 가능한 평가 장부로 묶음
- `scripts/publish_recon_to_notion.py`: Markdown 역구성 초안을 Notion 날짜 페이지로 게시
- `src/projects/autopark/`: 향후 수집/분석/적재 모듈 위치
- `data/`: 원본과 가공 데이터
- `runtime/`: 실행 로그, 스크린샷, Notion 임시 산출물
- `exports/`: 방송/대시보드/서버 이관용 최종 산출물

## Relationship to Buykings

Buykings의 기존 `buykings-morning` runner는 여러 아침 job을 묶는 상위
오케스트레이터이고, Autopark는 그 아래 붙을 독립 job으로 설계한다.

초기에는 수동 실행으로 검증하고, 안정화되면 `config/buykings-morning.json`에서
disabled job을 enabled로 바꾸어 상위 runner에 편입한다.
