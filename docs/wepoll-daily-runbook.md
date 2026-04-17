# Wepoll Daily Runbook

기준일: 2026-04-17

이 문서는 맥에서 수동으로 돌리는 `wepoll-panic` 운영 명령만 정리한다.  
당분간 모델 일관성을 위해 로컬 `ollama + gemma3:4b`를 기준으로 유지한다.

## 원칙

- 일별 additive는 **완전히 닫힌 날짜만** append 한다.
- 금/토/일처럼 아직 덜 쌓인 날짜는 넣지 않는다.
- 시장 데이터가 없으면 중단한다.
- 기존 날짜 값은 다시 계산하지 않고 새 날짜만 뒤에 붙인다.

## 현재 기준본

daily append 상태 파일은 아래를 기준으로 이어간다.

- `projects/wepoll-panic/state/appended_stance.csv`
- `projects/wepoll-panic/state/appended_quadrant.csv`
- `projects/wepoll-panic/state/appended_timeseries.csv`

Datawrapper spec은 아래 두 파일을 쓴다.

- `projects/wepoll-panic/charts/weekly-timeseries-2026-04-15-datawrapper.json`
- `projects/wepoll-panic/charts/weekly-bubble-2026-04-15-datawrapper.json`

## 가장 자주 쓰는 명령

### 1. 오늘 additive 확인 후 바로 반영

```bash
python3 scripts/run_wepoll_daily_append.py \
  --input /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv
```

이 명령은:

- 오늘 이전 날짜 중
- 게시물 수가 충분한 가장 최근 날짜를 자동 선택하고
- 시장 fetch -> LLM batch -> append -> prepared 갱신 -> Datawrapper publish

까지 한 번에 수행한다.

### 2. 특정 날짜만 강제로 append

```bash
python3 scripts/run_wepoll_daily_append.py \
  --input /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv \
  --target-date 2026-04-16
```

### 3. publish 없이 preview만 확인

```bash
python3 scripts/run_wepoll_daily_append.py \
  --input /ABS/PATH/TO/wepoll_stock_posts_YYYY-MM-DD_YYYY-MM-DD.csv \
  --target-date 2026-04-16 \
  --skip-publish
```

## 월요일 weekly

정식 weekly는 발표일 기준으로 직전 완료 일요일을 끝점으로 본다.

예:

- 발표일 `2026-04-20`
- 시계열 `2026-03-09 ~ 2026-04-19`
- 버블 `2026-04-13 ~ 2026-04-19`

prepared CSV만 다시 만들 때는:

```bash
WEPOLL_WEEKLY_REPORT_DATE=2026-04-20 \
RECENT_QUADRANT_SOURCE=/ABS/PATH/TO/recent_quadrant.csv \
python3 scripts/prepare_weekly_dw_assets.py
```

하지만 현재 운영에서는 weekly도 보통 daily append가 누적된 상태를 보고 Datawrapper를 검토하는 흐름으로 가는 편이 안전하다.

## 현재 수동 파트

당분간 수동으로 남는 것은 아래 두 가지다.

- 위폴 raw CSV 수급
- Datawrapper 결과 검토 및 최종 판단

나머지:

- 시장 데이터 fetch
- LLM 분류 실행
- append-only 계산
- prepared CSV 갱신
- Datawrapper publish

는 맥에서 명령 하나로 처리 가능하다.
