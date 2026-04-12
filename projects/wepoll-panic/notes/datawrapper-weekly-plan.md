# Wepoll Weekly Datawrapper Plan

기준일: 2026-04-12

`wepoll weekly`는 반복 발행이 분명한 만큼, 새 차트를 매주 만드는 대신 같은 `chart_id`를 계속 업데이트하는 운영이 맞다.

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
- export policy
  - 대표 파일은 `/exports/wepoll-panic/weekly/*.png`에 유지한다.
  - 발행 스냅샷은 `/exports/wepoll-panic/weekly/2026-04-12/`처럼 날짜 서브폴더에도 남긴다.
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

## 차트 1: Weekly Timeseries

- 차트 유형: `Datawrapper line chart`
- 데이터:
  - x축: `date`
  - 선 1: `psychology_index_0_100`
  - 선 2: `participation_index_0_100`
  - 막대: `post_count`
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

### 첫 세팅 체크리스트

1. `date`를 x축으로 둔다.
2. `psychology_index_0_100`, `participation_index_0_100`는 line으로 둔다.
3. `post_count`는 column/bar로 둔다.
4. 좌축은 0~100 고정, 게시물 수는 우축 자동 또는 최근 6주 최대값 기준으로 맞춘다.
5. range highlight는 `dw_weekly_timeseries_state_ranges_recent6w.csv`를 참고해 연속 구간 단위로 넣는다.
6. title/subtitle/source만 남기고 불필요한 note는 비운다.

## 차트 2: Weekly Bubble

- 차트 유형: `Datawrapper scatter plot`
- 데이터:
  - x축: `psychology_index_0_100`
  - y축: `participation_index_0_100`
  - 크기: `post_count`
  - 색: `state_label_ko`
  - 라벨: `day_label`
- 축 규칙:
  - x/y 모두 20~80 정도의 고정 범위 유지 권장
- 운영 메모:
  - 매주 최신 `week_range` 1개만 잘라서 같은 차트에 덮어쓴다.
  - `1일차~7일차` 라벨로 방송/PPT에서 날짜 읽기 부담을 줄인다.

### 첫 세팅 체크리스트

1. x축은 `psychology_index_0_100`, y축은 `participation_index_0_100`로 둔다.
2. bubble size는 `post_count`, label은 `day_label`로 둔다.
3. 색상은 `state_label_ko` 기준으로 고정한다.
4. x/y 범위는 주차별로 흔들지 말고 20~80 근처로 유지한다.
5. 기준선은 50/50 또는 기존 레퍼런스 이미지 기준으로 추가 검토한다.

## 발행 흐름

1. `python3 scripts/prepare_weekly_dw_assets.py`
2. timeseries/bubble chart CSV 갱신
3. `projects/wepoll-panic/charts/*.json`의 `chart_id`를 채운 뒤 `scripts/datawrapper_publish.py`로 update 발행
4. PNG export
5. Notion/보고서 반영
