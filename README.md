# Buykings

`Buykings`는 `Buykings Research` 작업 흐름 중, **데이터 시각화와 보고서 초안 제작에 특화된 저장소**다.

`Buykings Research`는 슈카친구들 안에서 다양한 데이터 분석 실험과 리서치 작업을 맡는 작은 분석 조직이라는 가정 위에서 움직인다. 그중 이 저장소는 분석 전체를 다루기보다, 다른 분석 저장소에서 정리된 결과를 받아 **Datawrapper 기반 피겨와 Notion 초안**으로 연결하는 역할에 집중한다.

## What This Repo Does

이 저장소의 핵심 역할은 세 가지다.

1. 다른 분석 폴더에서 정리된 최종 CSV를 받아온다.
2. Datawrapper에 바로 넣기 좋은 형태로 `prepared` CSV를 만든다.
3. 차트 publish, PNG export, Notion 초안 생성을 통해 발표용 산출물을 빠르게 만든다.

즉 목표는 "분석 자동화" 자체가 아니라, **반복 가능한 시각화 파이프라인**을 만드는 것이다.

## Current Tracks

현재는 두 개의 작업 축이 있다.

- `wepoll-panic`
  - 위폴 주간 운영용 시각화
  - 최근 6주 시계열, 주간 버블처럼 반복 갱신되는 템플릿 중심
- `wepoll-samsung`
  - 삼성 이벤트 결과 분석 시각화
  - 방송용 리포트 흐름에 맞춘 단발성 분석 차트 중심

## Repository Layout

```text
.
|-- README.md
|-- docs/
|-- exports/
|-- projects/
|   |-- wepoll-panic/
|   |   |-- incoming/
|   |   |-- prepared/
|   |   |-- charts/
|   |   `-- notes/
|   `-- wepoll-samsung/
|       |-- incoming/
|       |-- prepared/
|       |-- charts/
|       `-- notes/
|-- scripts/
`-- templates/
```

### Folder Roles

- `projects/<project>/incoming`
  - 외부 분석 저장소에서 넘어온 원본 CSV를 둔다.
  - 공개 저장소에는 올리지 않는 것을 기본 원칙으로 한다.
- `projects/<project>/prepared`
  - Datawrapper 업로드용 CSV를 둔다.
  - 원칙은 차트 1개당 CSV 1개다.
- `projects/<project>/charts`
  - 차트 스펙 JSON, 작업 메모, 발행된 chart ID를 둔다.
- `projects/<project>/notes`
  - 발표 흐름, 핵심 메시지, 후속 작업 메모를 둔다.
- `exports`
  - 최종 PNG 등 외부 공유 가능한 산출물을 둔다.
  - `wepoll-panic/weekly`는 대표 최신본과 날짜별 스냅샷을 함께 유지한다.
- `scripts`
  - Datawrapper publish, PNG export, Notion 초안 생성, weekly 자산 준비 같은 반복 작업 스크립트를 둔다.

## Standard Workflow

1. 상위 분석 저장소에서 결과 CSV를 가져온다.
2. `prepared/`에서 차트 친화적인 입력으로 정리한다.
3. `charts/`의 JSON spec을 기준으로 Datawrapper 차트를 생성하거나 갱신한다.
4. PNG를 `exports/`에 저장한다.
5. 필요하면 Notion 초안을 다시 생성한다.

## Public Repo Policy

이 저장소는 코드와 최종 시각화 산출물을 공개 가능한 범위로 관리한다.

- 커밋해도 되는 것
  - 스크립트
  - Datawrapper/Notion용 스펙 JSON
  - 공개 가능한 PNG, SVG 같은 최종 산출물
  - 분석 메모와 작업 문서
- 커밋하지 않는 것
  - `.env`와 API 키
  - 개인 로컬 경로가 박힌 임시 파일
  - 원본 `incoming` 데이터
  - 공개하기 어려운 개인 정보가 포함된 원천 자료

그래서 이 저장소의 스펙과 문서는 가능한 한 **상대 경로와 공개 가능한 참조만 사용**하도록 유지한다.

## Outputs We Already Use

현재 기준으로 이미 확인된 파이프라인은 아래와 같다.

- `Datawrapper -> PNG export -> Notion draft`
- `wepoll-panic`
  - 6주 시계열
  - 주간 버블
- `wepoll-samsung`
  - 이벤트 결과 차트
  - 활동성 차트
  - W2V PCA scatter
  - similar/fightin table

## Weekly Snapshot Policy

`wepoll-panic` weekly 산출물은 두 층으로 관리한다.

- 대표 최신본
  - `exports/wepoll-panic/weekly/timeseries.png`
  - `exports/wepoll-panic/weekly/bubble.png`
- 날짜별 스냅샷
  - `exports/wepoll-panic/weekly/YYYY-MM-DD/`

스냅샷 누적은 아래 스크립트로 처리한다.

```bash
python3 scripts/archive_weekly_exports.py --date YYYY-MM-DD
```

## Key Docs

- Datawrapper 운영 메모: `docs/datawrapper-notes.md`
- Datawrapper API 메모: `docs/api-next-steps.md`
- Notion 초안 파이프라인: `docs/notion-report-pipeline.md`
- 첫 실행 런북: `docs/first-run-playbook.md`
- 다음 차트 로드맵: `docs/next-chart-roadmap.md`

## Resume Point

현재 작업 기준점은 아래와 같다.

- 기준일: `2026-04-12`
- weekly 차트는 템플릿화가 진행 중이다.
- 삼성 이벤트 차트와 W2V/fightin 표는 방송용 초안에 연결돼 있다.
- `4/12` 데이터가 온전히 들어오면 weekly, post timing, W2V, fightin을 다시 갱신한다.

## Naming

이 저장소의 프로젝트 이름은 `Buykings`다.

문맥상 더 넓은 분석 조직을 가리킬 때는 `Buykings Research`라고 부르되, 이 저장소의 역할은 어디까지나 **시각화 제작과 보고서 초안화**에 있다.
