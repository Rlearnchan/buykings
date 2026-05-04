# Autopark

Autopark는 Buykings 아침 방송을 위한 시장 자료 수집, 해석, Notion 대시보드 발행, 방송 후 회고를 자동화하는 프로젝트입니다.

핵심 원칙은 단순합니다.

- 내부 엔진은 깊게 돌린다.
- 최종 Notion 발행물은 compact dashboard로 유지한다.
- LLM은 자료 구조, 순서, 카드명, 랭킹을 마음대로 바꾸지 않는다.
- 고급 판단은 큰 모델, 대량 요약과 문장 polish는 작은 모델에 맡긴다.

## What It Produces

매일 아침 파이프라인은 다음 산출물을 만듭니다.

- Notion 발행용 Markdown: `runtime/notion/YYYY-MM-DD/YY.MM.DD.md`
- 수집 원천과 가공 자료: `data/raw/YYYY-MM-DD/`, `data/processed/YYYY-MM-DD/`
- 차트/캡처 이미지: `exports/current/`, `runtime/screenshots/YYYY-MM-DD/`
- 품질 검사 리포트: `runtime/reviews/YYYY-MM-DD/dashboard-quality.*`
- 내부 장부 sourcebook: `docs/sourcebooks/YYYY-MM-DD-pipeline-sourcebook.md`
- 방송 후 회고: `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.*`

최종 Notion 대시보드는 크게 세 덩어리입니다.

1. `진행자용 요약`: 오늘 방송 큐시트
2. `자료 수집 > 1. 시장은 지금`: 지수, 금리, 원자재, 환율, FedWatch 등 시장 지도
3. `자료 수집 > 2. 미디어 포커스` 및 `3. 실적/특징주`: 기사, X, 캡처, 특징주 자료 창고

## Daily Pipeline

Docker scheduler가 KST 기준 지정 시각에 `run_live_dashboard_all_in_one.py`를 실행합니다.

```text
Docker scheduler
  -> browser/CDP health check
  -> source collection and screenshots
  -> Datawrapper chart update/export
  -> market radar
  -> evidence microcopy
  -> market focus brief
  -> editorial brief
  -> dashboard render
  -> quality gate
  -> Notion publish
  -> state mirror and logs
```

주요 단계는 아래와 같습니다.

| Step | Script | Role |
| --- | --- | --- |
| Preflight agenda | `build_market_preflight_agenda.py` | 수집 전에 오늘 확인할 시장 질문 후보를 만든다. |
| Collection | `collect_*`, `capture_*`, chart scripts | 뉴스, X, Finviz, CME, Yahoo, Datawrapper 자료를 모은다. |
| Market radar | `build_market_radar.py` | 수집 자료를 점수화하고 후보군으로 정리한다. |
| Evidence microcopy | `build_evidence_microcopy.py` | 후보 자료 100~200개를 짧은 한국어 요약으로 정리한다. |
| Market focus | `build_market_focus_brief.py` | 오늘 시장에서 중요한 초점과 false lead를 가른다. |
| Editorial | `build_editorial_brief.py` | 진행자용 스토리라인 3개와 방송 연결점을 만든다. |
| Dashboard render | `build_live_notion_dashboard.py` | renderer가 고정 포맷으로 publish Markdown을 만든다. |
| Dashboard microcopy | `build_dashboard_microcopy.py` | quote, 왜 중요한가, 카드 내용 문장만 다듬는다. |
| Quality gate | `review_dashboard_quality.py` | compact publish contract와 금지 토큰 노출을 검사한다. |
| Notion publish | `publish_recon_to_notion.py` | gate 통과 시 Notion 페이지를 교체 발행한다. |

## LLM Usage

LLM은 네 가지 종류의 일만 합니다.

신문사로 비유하면 다음과 같습니다.

- **Preflight agenda**: 조간 편집회의 전 뉴스 에디터입니다. 밤사이 무엇이 중요한지 훑고, 오늘 더 확인할 시장 질문과 취재 방향을 제안합니다. 최종 판단자는 아니고, 오늘의 가설 지도를 만듭니다.
- **Market focus**: 증권부 데스크입니다. 수집된 기사, 차트, 가격 반응, source gap을 보고 이 재료가 실제 시장 근거를 갖췄는지 검증합니다.
- **Editorial brief**: 편집국장입니다. 검증된 재료를 바탕으로 첫 5분 방송의 톱스토리, 순서, 흐름, 한국장 연결점을 정리합니다.
- **Dashboard microcopy**: 카피 에디터입니다. 구조나 순위는 바꾸지 않고, 최종 Notion에 들어갈 짧은 공개 문장만 매끄럽게 다듬습니다.

| Area | Default model | What it may do | What it must not do |
| --- | --- | --- | --- |
| Market preflight | `gpt-5.5` | 오늘 확인할 의제 후보 제안 | publish 구조 확정 |
| Evidence microcopy | `gpt-5-mini` | 각 자료의 핵심 한 줄 요약 | 자료 채택, 순서, 랭킹 결정 |
| Market focus | `gpt-5.5` | 리드 후보, source gap, false lead 판단 | renderer 포맷 변경 |
| Editorial brief | `gpt-5.5` | 스토리라인과 방송 연결점 판단 | publish 카드명/번호 변경 |
| Dashboard microcopy | `gpt-5-mini` | 최종 짧은 문장 polish | 구조, 순서, 자료명 변경 |

운영 환경에서는 보통 아래 env가 중요합니다.

```bash
AUTOPARK_EVIDENCE_MICROCOPY_ENABLED=1
AUTOPARK_EVIDENCE_MICROCOPY_MODEL=gpt-5-mini
AUTOPARK_MICROCOPY_ENABLED=1
AUTOPARK_MICROCOPY_MODEL=gpt-5-mini
AUTOPARK_EDITORIAL_MODEL=gpt-5.5
```

API 오류, timeout, invalid JSON이 나면 각 단계는 deterministic fallback으로 이어집니다. Notion 발행은 quality gate 정책을 따릅니다.

## Docker Automation

Autopark 운영 서비스는 루트의 `docker-compose.autopark.yml`에 있습니다.

- `autopark-browser`: 캡처용 Chromium/CDP 브라우저
- `autopark-publisher`: 아침 대시보드 scheduler
- `autopark-retrospective`: 방송 후 회고 scheduler

현재 아침 발행 스케줄:

- 메인 실행: `05:00 KST`
- 재시도: `05:20 KST`
- 브라우저: 호스트의 visible Chrome CDP 프로필을 Docker에서 제어

현재 소스 리버:

- Headline river: Yahoo ticker RSS + pre-flight agenda 확장, 공식 X 뉴스 계정, BizToc/Finviz fallback 순서
- Analysis river: Kobeissi Letter, Wall St Engine, Liz Ann Sonders, Charlie Bilello, Nick Timiraos, ZeroHedge, The Economist, IsabelNet, FactSet
- 기본 X lookback은 `72 hours`

자주 쓰는 상태 확인 명령:

```powershell
docker compose -f docker-compose.autopark.yml ps
docker logs --tail 80 buykings-autopark-publisher
docker logs --tail 80 buykings-autopark-retrospective
```

서비스 재기동:

```powershell
docker compose -f docker-compose.autopark.yml up -d --build autopark-browser autopark-publisher autopark-retrospective
```

주의: `autopark-browser`는 자동화가 사용하는 브라우저 세션입니다. 로그인/Cloudflare 상태가 필요한 사이트가 있어 임의로 끄지 않는 편이 좋습니다.

## Manual Runs

로컬에서 전체 대시보드 파이프라인을 한 번 돌릴 때:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_live_dashboard_all_in_one.py --date 2026-05-03
```

Notion 발행 없이 렌더와 검증만 볼 때:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_live_dashboard_all_in_one.py --date 2026-05-03 --skip-publish
```

이미 만들어진 Markdown의 품질만 검사할 때:

```powershell
.\.venv\Scripts\python.exe projects\autopark\scripts\review_dashboard_quality.py --date 2026-05-03 --input projects\autopark\runtime\notion\2026-05-03\26.05.03.md --json
```

Sourcebook hygiene check:

```powershell
.\.venv\Scripts\python.exe projects\autopark\scripts\build_pipeline_sourcebook.py --date 2026-05-03 --hygiene-check
```

## Repository Layout

```text
projects/autopark/
|-- charts/              # Datawrapper chart specs and chart ids
|-- config/              # source lists, calendar, chart config
|-- data/
|   |-- raw/             # collected source material, ignored by Git
|   `-- processed/       # radar, briefs, microcopy, ignored by Git
|-- docs/
|   |-- reference/       # editorial policy and local reference materials
|   |-- rehearsals/      # Docker rehearsal reports
|   `-- sourcebooks/     # internal pipeline ledgers
|-- exports/current/     # latest exported images, ignored by Git
|-- prepared/            # chart CSV inputs
|-- runtime/             # logs, screenshots, Notion markdown, reviews
|-- scripts/             # collection, rendering, quality, publish scripts
`-- tests/               # contract and regression tests
```

## Reference Materials

Durable editorial guidance lives in:

- `docs/reference/editorial-policy/`

Large local source materials are kept out of Git:

- `docs/reference/broadcast-samples/`: Viking PPTs and transcripts
- `docs/reference/book-notes/`: OCR/book extraction source files

If a raw reference becomes a reusable rule, distill it into Markdown under `docs/reference/editorial-policy/` instead of committing the original large file.

## Git Hygiene

Usually committed:

- scripts
- tests
- config
- docs and sourcebooks
- stable chart specs when intentionally changed

Usually not committed:

- `data/raw/*`
- `data/processed/*`
- `runtime/*`
- `exports/current/*`
- browser profiles
- PPT/PDF/RTF raw reference files
- API raw responses

Before committing, check:

```powershell
git status --short
python -m unittest discover -s projects/autopark/tests
```
