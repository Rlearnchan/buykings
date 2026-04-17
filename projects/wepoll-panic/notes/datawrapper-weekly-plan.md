# Wepoll Weekly Datawrapper Plan

기준일: 2026-04-16

이 문서는 차트 ID, 스냅샷 경로, 수동 편집 상태를 기록하는 운영 메모다.  
weekly 작업 원칙 자체는 `docs/wepoll-weekly-ops.md`를 기준으로 삼는다.

표시 범위 기준은 작업일이 아니라 **발표일(`WEPOLL_WEEKLY_REPORT_DATE`) 기준 직전 완료 일요일**이다.

`wepoll weekly`는 주차별 기록 보존이 중요하므로, **주가 바뀌면 새 dated chart를 만들고**, **같은 주 안에서는 그 chart_id를 계속 업데이트**하는 운영으로 간다.

## 준비된 데이터

- timeseries main CSV
  - `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w.csv`
- timeseries state ranges
  - `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w.csv`
- bubble latest week CSV
  - `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week.csv`

## 현재 차트

- weekly timeseries
  - chart id: `lt8ML`
  - public url: `https://datawrapper.dwcdn.net/lt8ML/4/`
  - edit url: `https://app.datawrapper.de/chart/lt8ML/edit`
  - current PNG: `exports/wepoll-panic/weekly/timeseries.png`
- weekly bubble
  - chart id: `txiva`
  - public url: `https://datawrapper.dwcdn.net/txiva/7/`
  - edit url: `https://app.datawrapper.de/chart/txiva/edit`
  - current PNG: `exports/wepoll-panic/weekly/bubble.png`
- folder path
  - `wepoll-panic / 260406`
- dated snapshot draft (new chart set)
  - specs:
    - `projects/wepoll-panic/charts/weekly-timeseries-2026-04-12-datawrapper.json`
    - `projects/wepoll-panic/charts/weekly-bubble-2026-04-12-datawrapper.json`
  - chart ids:
    - timeseries: `CkvG8`
    - bubble: `6Pk7H`
  - public urls:
    - timeseries: `https://datawrapper.dwcdn.net/CkvG8/`
    - bubble: `https://datawrapper.dwcdn.net/6Pk7H/`
  - prepared csv:
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w_2026-04-12.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w_2026-04-12.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week_2026-04-12.csv`
  - rule:
    - 기존 `lt8ML`, `txiva`는 템플릿/레퍼런스로 두고, 기준일별 새 chart를 만든다.
- this week draft set
  - specs:
    - `projects/wepoll-panic/charts/weekly-timeseries-2026-04-15-datawrapper.json`
    - `projects/wepoll-panic/charts/weekly-bubble-2026-04-15-datawrapper.json`
  - chart ids:
    - timeseries: `jRh1f`
    - bubble: `Dd29j`
  - public urls:
    - timeseries: `https://datawrapper.dwcdn.net/jRh1f/`
    - bubble: `https://datawrapper.dwcdn.net/Dd29j/`
  - prepared csv:
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w_2026-04-15.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w_2026-04-15.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week_2026-04-15.csv`
  - export snapshot:
    - `exports/wepoll-panic/weekly/2026-04-15/timeseries.png`
    - `exports/wepoll-panic/weekly/2026-04-15/bubble.png`
- 이번 주 작업 원칙
  - `2026-04-15` 시점 다음 weekly 작업은 이번 주용 새 dated chart를 먼저 만든다.
  - 그 뒤 같은 주 안의 수정은 새로 만든 그 chart에 반영한다.
  - 다음 주로 넘어가면 이번 주 chart는 보존하고 다시 새 set를 판다.
- export policy
  - 대표 파일은 `/exports/wepoll-panic/weekly/*.png`에 유지한다.
  - 발행 스냅샷은 `/exports/wepoll-panic/weekly/2026-04-15/`처럼 날짜 서브폴더에도 남긴다.
  - 스냅샷 복사는 `python3 scripts/archive_weekly_exports.py --date YYYY-MM-DD`로 처리한다.

## 현재 수동 수정 반영

- weekly timeseries `lt8ML`
  - 제목: `위폴은 지금: 6주 시계열`
  - 현재 타입: `multiple-lines`
  - theme: `datawrapper-high-contrast`
  - 50 기준선 2개와 최근 구간 오렌지 x-range highlight가 들어갔다.
  - 현재는 게시물 수가 bar가 아니라 line으로 남아 있다.
- weekly bubble `txiva`
  - 제목: `위폴은 지금: 지난 주 7일`
  - x/y 범위는 모두 `0~100`
  - 50/50 점선 기준선과 `공포/탐욕/신중/낙관` 텍스트가 들어갔다.
  - 현재 폴더는 `wepoll-panic / 260406`

## Datawrapper 확인 메모

`2026-04-15` 기준으로 Datawrapper 원격 차트를 다시 확인했다.

- `txiva`, `6Pk7H` 모두 x/y 축 범위가 `0~100`으로 고정돼 있다.
- `txiva`, `6Pk7H` 모두 50/50 점선 기준선과 사분면 텍스트가 들어가 있다.
- `lt8ML`, `CkvG8` 모두 좌축은 `0~100` 고정이고 50 기준선 2개가 들어가 있다.
- `CkvG8`는 `2026-04-06 ~ 2026-04-12` 구간 x-range highlight가 반영돼 있다.

## 차트 1: Weekly Timeseries

- 차트 유형: `Datawrapper line chart`
- 데이터:
  - x축: `date`
  - 선 1: `심리(Bear-Bull) 지수`
  - 선 2: `참여 지수`
  - 막대: `게시물 수`
- 표시 범위:
  - 최근 42일 고정
- 배경:
  - `dw_weekly_timeseries_state_ranges_recent6w.csv`를 참고해 연속 구간 단위 range highlight 적용
  - 색상 기준:
    - 공포: 연한 빨강
    - 탐욕: 연한 노랑
    - 신중: 연한 회색
    - 낙관: 연한 파랑
- 운영 메모:
  - 같은 `chart_id`를 유지하며 CSV만 덮어쓴다.
  - export PNG는 대표 파일을 overwrite 한다.
  - publish 직후 `archive_weekly_exports.py`로 날짜 스냅샷을 남긴다.
  - 표시 구간은 `WEPOLL_WEEKLY_REPORT_DATE` 기준 직전 완료 일요일까지의 42일이다.

### 첫 세팅 체크리스트

1. `date`를 x축으로 둔다.
2. `심리(Bear-Bull) 지수`, `참여 지수`는 line으로 둔다.
3. `게시물 수`는 column/bar로 둔다.
4. 좌축은 0~100 고정, 게시물 수는 우축 자동 또는 최근 6주 최대값 기준으로 맞춘다.
5. range highlight는 `dw_weekly_timeseries_state_ranges_recent6w.csv`를 참고해 연속 구간 단위로 넣는다.
6. title/subtitle/source만 남기고 불필요한 note는 비운다.

## 차트 2: Weekly Bubble

- 차트 유형: `Datawrapper scatter plot`
- 데이터:
  - x축: `심리(Bear-Bull) 지수`
  - y축: `참여 지수`
  - 크기: `게시물 수`
  - 색: `state_label_ko`
  - 라벨: `day_label`
- 축 규칙:
  - x/y 모두 `0~100` 고정
- 운영 메모:
  - 같은 주 안에서는 발표 기준 직전 완료 주간 `week_range` 1개만 잘라 그 주의 chart에 덮어쓴다.
  - 다음 주 작업은 새 dated chart를 만들어 그쪽으로 발행한다.
  - `1일차~7일차` 라벨로 방송/PPT에서 날짜 읽기 부담을 줄인다.

### 첫 세팅 체크리스트

1. x축은 `심리(Bear-Bull) 지수`, y축은 `참여 지수`로 둔다.
2. bubble size는 `게시물 수`, label은 `day_label`로 둔다.
3. 색상은 `state_label_ko` 기준으로 고정한다.
4. x/y 범위는 `0~100`으로 고정한다.
5. 기준선은 50/50 또는 기존 레퍼런스 이미지 기준으로 추가 검토한다.

## 발행 흐름

1. `WEPOLL_WEEKLY_REPORT_DATE=YYYY-MM-DD python3 scripts/prepare_weekly_dw_assets.py`
2. timeseries/bubble chart CSV 갱신
3. 이번 주용 `projects/wepoll-panic/charts/*YYYY-MM-DD-datawrapper.json`을 만들거나 갱신한 뒤 `scripts/datawrapper_publish.py`로 발행
4. PNG export
5. Notion/보고서 반영
