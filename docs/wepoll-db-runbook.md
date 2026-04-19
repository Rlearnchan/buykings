# Wepoll DB Runbook

기준일: 2026-04-19

이 문서는 위폴 CSV 원본과 현재까지 산출한 지수를 Postgres에 적재하는 운영 기준을 정리한다.

핵심 원칙은 간단하다.

- 스레드에는 계속 CSV를 던진다.
- 원본 CSV는 사람이 보기 쉬운 파일 형태로 유지한다.
- 뒤에서는 Postgres를 정본 저장소처럼 사용한다.
- 차트용 CSV와 PNG는 여전히 별도 산출물로 유지한다.

## 저장 원칙

현재는 아래처럼 역할을 나눈다.

- 원본 게시물 정본
  - `wepoll_raw_posts`
- 원본 파일 이력
  - `wepoll_source_files`
- 일별 feature 정본
  - `wepoll_daily_features`
- 일별 최종 지수 정본
  - `wepoll_daily_indices`

즉:

- `Downloads/*.csv` 같은 raw 파일은 입력
- `projects/wepoll-panic/state/*.csv`는 현재 운영 상태 캐시
- Postgres는 누적 정본

## 스키마

스키마 파일:

- `db/wepoll_postgres.sql`

적용 테이블:

- `wepoll_source_files`
- `wepoll_raw_posts`
- `wepoll_daily_features`
- `wepoll_daily_indices`

## 의존성

현재 적재 스크립트는 `psycopg`를 사용한다.

```bash
python3 -m pip install psycopg[binary]
```

그리고 Postgres 연결 문자열을 준비한다.

```bash
export DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME'
```

## 첫 세팅

스키마를 만들면서 첫 적재를 할 때:

```bash
python3 scripts/wepoll_sync_postgres.py \
  --init-schema \
  --raw-csv /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv
```

이 명령은:

- raw CSV를 `wepoll_source_files`, `wepoll_raw_posts`에 upsert
- 현재 `projects/wepoll-panic/state/appended_stance.csv`를 `wepoll_daily_features`에 upsert
- 현재 `projects/wepoll-panic/state/appended_quadrant.csv`를 `wepoll_daily_indices`에 upsert

## 평소 운영

새 CSV를 스레드에서 받아서 daily append나 weekly 작업을 마친 뒤에는 아래처럼 적재한다.

```bash
python3 scripts/wepoll_sync_postgres.py \
  --raw-csv /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv
```

원본 CSV를 따로 새로 안 넣고, 현재 state만 DB에 다시 맞추고 싶으면:

```bash
python3 scripts/wepoll_sync_postgres.py
```

이 경우 raw post upsert는 건너뛰고, state 기반 일별 feature / 지수만 다시 맞춘다.

## 입력 포맷

raw ingest는 현재 두 포맷을 모두 흡수한다.

- 구형
  - `글ID`, `작성자ID_익명`
- 신형
  - `ID`, `작성자ID`, `게시판`, `구분`, `원글ID`, `깊이`, `답글코드`

그리고 현재 DB 적재에서는 기본적으로:

- `구분 == 글`
- `깊이 == 0`

만 원본 게시물로 본다.

## 추천 운영 흐름

1. 스레드에 raw CSV를 던진다.
2. daily append 또는 weekly 작업을 수행한다.
3. 결과를 검토한다.
4. 적재 스크립트로 raw/state를 Postgres에 반영한다.

즉 CSV는 여전히 가장 편한 입력 방식이고, DB는 그 뒤에 누적 정리하는 저장소로 쓴다.
