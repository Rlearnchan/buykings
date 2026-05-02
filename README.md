# Buykings

`Buykings`는 아침 방송과 위폴 관련 데이터 운영을 묶는 상위 자동화 저장소다.

이 저장소의 역할은 단순히 차트 이미지를 보관하는 것이 아니라, 하위 서브 프로젝트들이 각자 가진 수집/분석/발행 루틴을 한곳에서 실행하고 관리하는 것이다.

현재 대표 서브 프로젝트는 두 가지다.

- `projects/autopark`: 매일 아침 시장/뉴스/차트 자료를 모아 방송용 Notion 대시보드를 만들고, 방송 후 회고까지 연결한다.
- `projects/wepoll-panic`: 위폴 게시물 원본 CSV를 받아 일별 심리/참여 지수와 주간 시각화를 누적 관리한다.

즉 이 레포는 **Buykings 운영 자동화 오케스트레이터 + 서브 프로젝트별 발행 자산 저장소**에 가깝다.

## What We Publish

현재 바깥으로 나가는 핵심 산출물은 크게 세 갈래다.

- Autopark 일별 방송 대시보드
- 위폴 최근 6주 시계열
- 위폴 지난 주 7일 버블 차트

Autopark는 Notion과 방송 준비 자료 중심이고, 위폴 지수는 `위폴은 지금`이라는 별도 트랙 안에서 운영된다.

## How The Workflow Works

상위 운영 흐름은 아래처럼 이해하면 된다.

1. 상위 runner 또는 Codex/Windows Task Scheduler가 날짜별 job을 실행한다.
2. 각 서브 프로젝트는 자기 폴더 안에서 raw/processed/runtime/export 산출물을 만든다.
3. Datawrapper, Notion, YouTube transcript, SQLite 같은 외부 연동은 공통 스크립트와 환경변수를 통해 처리한다.
4. 품질검수와 회고 결과는 runtime/docs에 남기고 다음 실행의 입력으로 일부 반영한다.
5. 공개 가능한 코드, 차트 스펙, 운영 문서, 최종 PNG만 Git에 남긴다.

핵심 원칙은 두 가지다.

**서브 프로젝트별 산출물 경계를 지키고, 기존 발행값은 명시적 요청 없이는 흔들지 않는다.**

## What Lives In This Repo

```text
.
|-- README.md
|-- db/
|-- docs/
|-- exports/
|-- logo/
|-- projects/
|   |-- autopark/
|   |   |-- charts/
|   |   |-- config/
|   |   |-- data/
|   |   |-- docs/
|   |   |-- exports/
|   |   |-- runtime/
|   |   `-- scripts/
|   `-- wepoll-panic/
|       |-- charts/
|       |-- incoming/
|       |-- notes/
|       |-- prepared/
|       `-- state/
`-- scripts/
```

각 폴더의 역할은 이렇다.

- `projects/autopark`
  - morning broadcast dashboard automation workspace
  - collects market/news/chart inputs, builds an LLM editorial brief, publishes a daily Notion dashboard, and writes post-broadcast review artifacts
  - owns its charts, config, data, docs, exports, runtime, and project scripts
- `projects/wepoll-panic/state`
  - 현재까지 누적된 일별 지수 상태값
  - daily/weekly append의 기준본
- `projects/wepoll-panic/prepared`
  - Datawrapper에 바로 넣는 CSV
- `projects/wepoll-panic/charts`
  - Datawrapper 차트 스펙과 `chart_id`
- `projects/wepoll-panic/notes`
  - weekly 운영 메모와 작업 맥락
- `exports/wepoll-panic/weekly`
  - 최신 PNG와 날짜별 스냅샷
- `scripts`
  - append, publish, PNG export, DB 적재 같은 반복 작업 스크립트
- `db`
  - SQLite / schema 같은 로컬 저장 구조

## Current Storage Model

원본과 산출물은 지금 이렇게 나뉜다.

- raw input
  - 사람이 전달한 위폴 CSV
  - 주로 `Downloads/` 같은 로컬 경로에 있음
- working state
  - `projects/wepoll-panic/state/*.csv`
- publication assets
  - `projects/wepoll-panic/prepared/*.csv`
  - `exports/wepoll-panic/weekly/*.png`
- local database
  - `db/wepoll.sqlite3`

즉 입력은 CSV로 받고, 운영 상태는 CSV로 유지하면서, 뒤에서는 SQLite에도 같이 적재하는 구조다.

## Main Scripts

처음 보는 사람 기준으로 가장 중요한 스크립트는 이 셋이다.

- `scripts/run_wepoll_daily_append.py`
  - 하루치 additive append 실행
- `scripts/append_weekly_marketblend.py`
  - 기존 기준을 유지한 채 새 날짜를 뒤에 붙이는 핵심 로직
- `scripts/export_wepoll_weekly_png.py`
  - weekly PNG를 고정된 규격으로 export

DB 적재는 아래 스크립트를 쓴다.

- `scripts/wepoll_sync_sqlite.py`
  - raw CSV / state를 SQLite에 적재
- `scripts/wepoll_download_playwright.py`
  - 위폴 특수 계정 데이터 다운로드 페이지를 Playwright로 자동화하는 초안
- `scripts/wepoll_fetcher_daemon.mjs`
  - 로그인된 Playwright 브라우저를 장기 실행하며 `/health`, `/download`를 제공하는 fetcher
- `scripts/run_wepoll_daily_from_fetcher.py`
  - fetcher에서 raw CSV를 받아 daily append와 SQLite sync를 연달아 실행
- `scripts/run_buykings_morning.py`
  - top-level morning manifest를 읽고 enabled jobs를 순서대로 실행

## PNG Policy

weekly PNG는 항상 같은 기준으로 관리한다.

- 공통 export 폭: `600`
- 공통 scale: `2`
- 로고 top: `15px`
- 로고 right: `30px`
- 시계열 로고 높이 비율: `0.10`
- 버블 로고 높이 비율: `0.08`

즉 차트 종류가 달라도 로고 윗선은 같은 위치에 놓이도록 맞춘다.

## Key Docs

상세 운영 규칙은 아래 문서를 보면 된다.

- [docs/wepoll-weekly-ops.md](docs/wepoll-weekly-ops.md)
  - weekly 발행 규칙, append 원칙, Datawrapper 흐름
- [docs/wepoll-daily-runbook.md](docs/wepoll-daily-runbook.md)
  - daily append 실행 방식
- [docs/wepoll-db-runbook.md](docs/wepoll-db-runbook.md)
  - raw CSV / state를 SQLite에 적재하는 방식
- [docs/datawrapper-notes.md](docs/datawrapper-notes.md)
  - Datawrapper 운영 메모
- [docs/wepoll-automation-plan.md](docs/wepoll-automation-plan.md)
  - Windows 서버 + Docker + 위폴 수급/Notion 자동화 계획
- [docs/wepoll-long-lived-fetcher.md](docs/wepoll-long-lived-fetcher.md)
  - 네이버 소셜 로그인 대응용 장기 실행 fetcher 운영안
- [docs/wepoll-windows-server-runbook.md](docs/wepoll-windows-server-runbook.md)
  - Windows 서버에서 fetcher와 daily batch를 운영하는 절차
- [projects/autopark/README.md](projects/autopark/README.md)
  - Autopark daily dashboard, LLM editorial brief, FedWatch split tables, and post-broadcast retrospective loop
- [projects/autopark/docs/autopark-editorial-retrospective-runbook.md](projects/autopark/docs/autopark-editorial-retrospective-runbook.md)
  - Autopark 편집장/방송 회고/피드백 반영 운영 기준
- [docs/wepoll-panic-migration.md](docs/wepoll-panic-migration.md)
  - `wepoll-panic`을 Windows 서버로 먼저 옮기는 1차 마이그레이션 기준
- [docs/buykings-morning-architecture.md](docs/buykings-morning-architecture.md)
  - `buykings-morning` 상위 오케스트레이터 구조

Windows 서버 넘김용 starter 세트:

- [ops/windows/README.md](ops/windows/README.md)
  - Windows 서버 Codex handoff와 PowerShell starter scripts

## Typical Commands

daily append:

```bash
python3 scripts/run_wepoll_daily_append.py \
  --input /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv
```

weekly PNG export:

```bash
python3 scripts/export_wepoll_weekly_png.py timeseries CHART_ID OUTPUT.png
python3 scripts/export_wepoll_weekly_png.py bubble CHART_ID OUTPUT.png
```

SQLite sync:

```bash
python3 scripts/wepoll_sync_sqlite.py \
  --init-schema \
  --raw-csv /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv
```

## Public Repo Policy

이 저장소는 공개 가능한 코드와 운영 문서를 중심으로 관리한다.

커밋하는 것:

- 스크립트
- 차트 스펙
- 운영 문서
- 공개 가능한 PNG
- 누적 state / prepared CSV

커밋하지 않는 것:

- `.env`
- API 키
- raw 입력 CSV
- SQLite DB 파일
- 임시 파일

즉 GitHub에는 **운영 방식과 발행 자산**을 남기고, raw 입력과 로컬 DB는 로컬에 둔다.
