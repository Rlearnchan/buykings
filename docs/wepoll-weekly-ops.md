# Wepoll Weekly Ops

기준일: 2026-04-16

이 문서는 `wepoll-panic`의 주간 시각화 작업, 즉 **"위폴은 지금"** 운영 규칙을 정리한 전담 문서다.  
새 스레드에서 weekly 작업만 맡길 때, 이 문서를 먼저 읽는 것을 기본 전제로 한다.

## Scope

`위폴은 지금`은 아래 두 산출물을 뜻한다.

- 최근 6주 시계열
- 지난 주 7일 버블 차트

이 트랙은 삼성 이벤트 분석과 분리해서 운영한다.  
주간 작업에서는 weekly 데이터 처리와 weekly 차트 작성에만 집중한다.

## Core Rule

가장 중요한 규칙은 하나다.

**기존에 발행된 시계열 값은 절대 다시 정규화하거나 평탄화하거나 재보정하지 않는다.**

즉 weekly 작업은:

1. 기존 기준본을 고정해 둔 채
2. 새로 들어온 1주일치만
3. 같은 공식으로 계산해서
4. 뒤에 이어 붙이는 append 방식

으로 처리해야 한다.

하면 안 되는 것:

- 전체 기간을 다시 계산해서 과거 값까지 흔드는 것
- 최신 데이터가 들어왔다는 이유로 기준선이나 z-score 기준을 새로 잡는 것
- 시장 데이터가 없는데 fallback 값으로 weekly 공식 산출물을 밀어 넣는 것

## Required Inputs

사람이 weekly 작업을 시작할 때 반드시 넣어줘야 하는 입력은 아래 네 묶음이다.

### 1. 위폴 원본 데이터

- 최근 1주 이상을 포함하는 위폴 게시물 원본 CSV
- 최소한 지난 주 7일 전체를 덮어야 한다

예:

- `wepoll_stock_2026-03-30_2026-04-13.csv`

### 2. 기존 기준본

이전까지 이미 발행된 값을 담은 기준 파일들이다. 이 값들은 바꾸면 안 된다.

- `../wepoll-panic/output/yearly_hybrid_batch_v4/anchor_calibrated_stance_v10r.csv`
- `../wepoll-panic/output/yearly_hybrid_batch_v4/psychology_participation_postcount_timeseries_append_2026-04-05.csv`
- `../wepoll-panic/output/yearly_hybrid_batch_v4/anchor_quadrant_v10r_marketblend_labels_append_2026-04-05.csv`
- `../wepoll-panic/output/yearly_hybrid_batch_v4/market_daily_normalized.csv`

### 3. 시장 데이터

정식 weekly는 `인베스팅닷컴` 시장 데이터가 꼭 필요하다.

- 코스피지수 과거 데이터 CSV
- 코스닥 과거 데이터 CSV
- KOSPI Volatility 과거 데이터 CSV

이 데이터는 참여 지수 산출에서 market turnover / volatility 기준을 유지하는 데 필요하다.

### 4. 기존 차트 템플릿

weekly 차트는 이미 손으로 다듬은 스타일이 있으므로, 새 dated 세트를 만들 때도 기존 스타일을 최대한 복제해야 한다.

- 기존 timeseries template: `lt8ML`
- 기존 bubble template: `txiva`

dated 세트를 새로 만들 때도 스타일 출발점은 이 둘이다.

## Hard Stop Conditions

아래 조건이면 weekly 정식 작업은 진행하지 않는다.

### 시장 데이터가 없는 경우

아래 중 하나라도 없으면 **중단**한다.

- 코스피 CSV 없음
- 코스닥 CSV 없음
- VKOSPI CSV 없음
- 필요한 날짜 범위를 덮지 못함

이 경우에는 억지로 fallback weekly를 만들지 말고, 아래처럼 명시적으로 끊는다.

> 시장 데이터가 없어 정식 weekly 산출을 진행하지 못했습니다.  
> 기존 수치를 유지해야 하므로 fallback 재산출은 하지 않습니다.

### 위폴 원본 데이터가 덜 들어온 경우

weekly 차트의 표시 범위는 **작업일**이 아니라 **발표 기준일**을 따른다.

예를 들어 발표가 `2026-04-20` 월요일이면:

- weekly 종료일은 직전 일요일인 `2026-04-19`
- 6주 시계열은 `2026-03-09 ~ 2026-04-19`
- 버블 차트는 `2026-04-13 ~ 2026-04-19`

즉 weekly 기준일은 **발표 주간이 완전히 닫힌 일요일**로 잡는다.
그 날짜 범위를 온전히 못 덮으면 정식 산출은 중단한다.

## Weekly Pipeline

weekly 작업은 아래 순서로 이해하면 된다.

1. 사람이 데이터 투입
2. 전처리
3. daily features 산출
4. 기존 기준 유지 append
5. Datawrapper용 CSV 생성
6. Datawrapper 차트 발행
7. PNG export
8. 필요 시 Notion 초안 반영

## Operational Principle

weekly는 **재산출(recompute)** 이 아니라 **이어붙이기(append)** 다.

실무적으로는:

- `4/5`까지 기존 published 값은 고정
- `4/6 ~ 4/12`만 새로 계산
- 새 주간 값을 기존 기준 뒤에 append

이 원칙이 지켜졌는지 반드시 검증해야 한다.

## Canonical Script

append 전용 스크립트는 아래 파일이다.

- `scripts/append_weekly_marketblend.py`

이 스크립트의 역할은:

- 기존 기준본 `stance`를 읽고
- 새로 계산된 `daily features`를 읽고
- 기존 published timeseries를 읽고
- 기존 normalized market + 최신 인베스팅닷컴 CSV를 합친 뒤
- **기존 날짜 값은 유지한 채 새 날짜만 append** 하는 것이다

즉 weekly 운영에서 가장 중요한 스크립트는 이 파일이다.

## Recommended Run Order

### Step 1. 새 원본을 정리한다

- 위폴 CSV를 확인한다
- 기준일을 정한다
- 덜 들어온 날짜는 제외한다

예:

- 발표일이 `2026-04-20`인데 `2026-04-19` 데이터가 아직 비어 있으면 weekly 정식 산출은 중단한다.

### Step 2. 새 구간의 daily features를 만든다

이 단계는 `wepoll-panic` 쪽 전처리/라벨링 코드를 사용한다.

핵심은:

- 새 주간 구간의 일별 feature만 만들 것
- 과거 구간을 다시 손대지 말 것

### Step 3. append-only market-blend를 수행한다

`scripts/append_weekly_marketblend.py`를 사용해:

- 기존 published 시계열은 고정
- 새 주간만 append

### Step 4. Datawrapper용 CSV를 만든다

최종 출력은 아래 세 파일이다.

- `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w_YYYY-MM-DD.csv`
- `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w_YYYY-MM-DD.csv`
- `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week_YYYY-MM-DD.csv`

여기서:

- timeseries는 항상 **latest 6주만 남긴다**
- bubble은 항상 **발표 주간 직전 7일만 남긴다**

### Step 5. Datawrapper 차트를 발행한다

weekly 차트는 **주차 단위로 새 dated 세트를 만들고**,  
**같은 주 안에서는 그 dated chart를 계속 업데이트**한다.

즉:

- 같은 주간 업데이트라면 그 주의 `chart_id`를 계속 써도 된다
- 다른 주간 작업으로 넘어가면 기존 주차 chart는 보존하고 새 chart를 만든다

예:

- `weekly-timeseries-2026-04-12-datawrapper.json`
- `weekly-bubble-2026-04-12-datawrapper.json`

그리고 기존 손작업 스타일을 유지하기 위해, 가능하면:

- 기존 chart metadata를 복제하거나
- 기존 chart를 템플릿처럼 참고해 새 chart를 만든다

### Step 6. PNG를 저장한다

dated weekly PNG는 아래 구조를 쓴다.

- `exports/wepoll-panic/weekly/YYYY-MM-DD/timeseries.png`
- `exports/wepoll-panic/weekly/YYYY-MM-DD/bubble.png`

대표 최신본을 따로 갱신할지 여부는 상황에 따라 결정하되,  
dated snapshot은 반드시 남긴다.

우측 상단 빈 공간에 `Buykings Research` 로고를 고정 배치하려면 Datawrapper 내부 설정 대신 export 후처리를 쓴다.

```bash
python3 scripts/export_wepoll_weekly_png.py timeseries CHART_ID OUTPUT.png
python3 scripts/export_wepoll_weekly_png.py bubble CHART_ID OUTPUT.png
```

현재 weekly 고정값은 아래다.

- 공통 export 폭: `600`
- 공통 export scale: `2`
- 로고 top 위치: `15px`
- 로고 right 위치: `30px`
- 시계열 로고 높이 비율: `0.10`
- 버블 로고 높이 비율: `0.08`

즉 weekly PNG는 차트 종류가 달라도 로고 윗선이 같은 픽셀 위치에 놓이도록 맞춘다.

## Validation Checklist

weekly 작업 후에는 아래를 반드시 확인한다.

### 1. 과거 값 보존

기존 published 마지막 날짜까지 값이 완전히 같아야 한다.

예:

- `2026-04-05`까지 diff count가 `0`

이게 깨지면 weekly 결과는 폐기하고 다시 본다.

### 2. 새 구간 길이 확인

- bubble은 발표 기준 주간 `월~일` 7일치인지
- timeseries는 발표 기준 종료일을 끝점으로 정확히 42일인지

### 3. 시장 데이터 반영 확인

- 코스피 / 코스닥 / VKOSPI가 실제로 읽혔는지
- 거래량 기반 값이 append에 반영됐는지

### 4. 상태값 및 라벨 규칙 확인

표시 규칙은 아래로 통일한다.

- `participation` -> `참여 지수`
- `psy` -> `심리(Bear-Bull) 지수`
- `post` -> `게시물 수`
- `경계` -> `신중`

### 5. 축과 매핑 확인

버블 차트는 아래처럼 고정한다.

- x축: `심리(Bear-Bull) 지수`
- y축: `참여 지수`
- 크기: `게시물 수`
- x/y 범위: `0~100`

## Automation Note

`scripts/prepare_weekly_dw_assets.py`는 `WEPOLL_WEEKLY_REPORT_DATE` 환경변수를 받는다.

- 이 값은 **발표일**이다.
- 스크립트는 여기서 직전 완료 일요일을 계산해 시계열 42일과 버블 7일 범위를 정한다.
- 필요한 날짜가 하나라도 비면 에러로 중단한다.

예:

- `WEPOLL_WEEKLY_REPORT_DATE=2026-04-20`
  - timeseries: `2026-03-09 ~ 2026-04-19`
  - bubble: `2026-04-13 ~ 2026-04-19`

## 2026-04-12 Example

`2026-04-12` dated weekly 작업은 이 원칙으로 이미 한 번 수행됐다.

대표 산출물:

- `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w_2026-04-12.csv`
- `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w_2026-04-12.csv`
- `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week_2026-04-12.csv`
- `exports/wepoll-panic/weekly/2026-04-12/timeseries.png`
- `exports/wepoll-panic/weekly/2026-04-12/bubble.png`

Datawrapper dated set:

- timeseries: `CkvG8`
- bubble: `6Pk7H`

이 run에서는 기존 published 값과 비교해 `2026-04-05`까지 diff가 `0`인지 확인한 뒤 append를 확정했다.

## What The Next Thread Should Do

새 스레드가 weekly를 맡으면, 아래 순서로 움직이면 된다.

1. 이 문서를 읽는다.
2. 새로 들어온 위폴 CSV와 시장 CSV 3개가 모두 있는지 확인한다.
3. 기준일을 정한다.
4. 기존 published 값은 고정한다.
5. 새 구간만 append한다.
6. 이번 주용 dated weekly 차트를 새로 만들고, 같은 주 안에서는 그 chart를 업데이트한다.
7. PNG를 저장한다.
8. 입력이 부족하면 억지로 fallback 하지 말고, 왜 중단됐는지 명시한다.

## One-Line Rule

weekly는 **"기존 값 유지 + 새 1주 append"** 이다.  
입력이 부족하면 **"못 한다고 명확히 끊는 것"** 이 정답이다.
