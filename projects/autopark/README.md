# Autopark

Autopark는 Buykings 아침방송 준비 자동화를 위한 서브 프로젝트다.

초기 목표는 매일 아침 확인해야 하는 시장 데이터를 수집해 Datawrapper 차트로 만들고,
원문/스크린샷은 내부 증빙으로 보관하며, Wepoll 지수와 함께 스토리 라인 후보를 만든 뒤
Notion 적재와 서버 이관까지 이어지는 대시보드형 파이프라인을 만드는 것이다.

## Current Scope

지금 단계는 구현보다 기획과 운영 골격을 먼저 고정한다.

- 고정 차트는 API/구조화 데이터와 Datawrapper 제작 흐름으로 전환
- 사이트별 캡처 위치와 해석 노하우는 내부 증빙 매니페스트에 축적
- 원문/스크린샷/메타데이터를 날짜별로 보관
- Wepoll 지수 산출물과 결합할 인터페이스 정의
- 스토리 라인 후보 3개를 생성하기 위한 입력 구조 정의
- Notion 적재와 서버 이관을 별도 단계로 분리

## Quick Start

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
