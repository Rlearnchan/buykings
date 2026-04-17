# Buykings

`Buykings`는 현재 기준으로 `wepoll-panic` 지수 산출과 주간 시각화 운영에 집중하는 저장소다.

## What This Repo Does

이 저장소의 핵심 역할은 세 가지다.

1. 위폴 원본/시장 데이터를 받아 지수 append 작업을 수행한다.
2. Datawrapper에 바로 넣기 좋은 `prepared` CSV를 만든다.
3. 차트 publish와 PNG export를 통해 주간 시각화를 유지한다.

즉 목표는 **반복 가능한 위폴 지수 운영 파이프라인**을 만드는 것이다.

## Current Tracks

현재 작업 축은 하나다.

- `wepoll-panic`
  - 위폴 지수 산출과 주간 운영용 시각화
  - 최근 6주 시계열, 주간 버블, daily additive append

## Repository Layout

```text
.
|-- README.md
|-- docs/
|-- exports/
|-- projects/
|   `-- wepoll-panic/
|       |-- incoming/
|       |-- prepared/
|       |-- charts/
|       |-- notes/
|       `-- state/
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
  - Datawrapper publish, PNG export, daily append, weekly 자산 준비 같은 반복 작업 스크립트를 둔다.

## Standard Workflow

1. 상위 분석 저장소에서 결과 CSV를 가져온다.
2. `prepared/`에서 차트 친화적인 입력으로 정리한다.
3. `charts/`의 JSON spec을 기준으로 Datawrapper 차트를 생성하거나 갱신한다.
4. PNG를 `exports/`에 저장한다.

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

- `Investing.com fetch -> LLM batch -> append -> Datawrapper publish`
- `wepoll-panic`
  - 6주 시계열
  - 주간 버블

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
- 위폴 주간 운영 문서: `docs/wepoll-weekly-ops.md`
- 위폴 daily 운영 명령: `docs/wepoll-daily-runbook.md`

## Resume Point

현재 작업 기준점은 아래와 같다.

- 기준일: `2026-04-16`
- weekly 차트는 이 저장소에서 주차별 dated set로 운영한다.
- 자동화 시에는 `WEPOLL_WEEKLY_REPORT_DATE`를 발표일로 넘기고, 차트 범위는 직전 완료 일요일 기준으로 계산한다.
- 같은 주 안에서는 해당 주의 chart를 업데이트하고, 주가 바뀌면 새 chart 세트를 만든다.
- daily additive는 맥에서 `gemma3:4b` 기준으로 수동 실행한다.
- 위폴 raw CSV 수급과 최종 결과 검토만 수동으로 남아 있다.

## Naming

이 저장소의 프로젝트 이름은 `Buykings`다.

이 저장소의 역할은 현재 기준으로 **위폴 지수 산출과 Datawrapper 운영**에 있다.
