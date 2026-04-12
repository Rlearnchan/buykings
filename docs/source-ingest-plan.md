# Source Ingest Plan

이 문서는 상위 분석 저장소에서 어떤 CSV를 이 시각화 저장소로 가져오면 좋은지 정리한 인입 계획서다.

기준 작업 폴더:

- `../wepoll-panic`
- `../wepoll-samsung`

확인 기준일:

- 2026-04-11

## Summary

현재 기준으로 보면 두 프로젝트의 상태는 다르다.

- `wepoll-samsung`은 이벤트 결과 자체를 설명하는 핵심 차트는 이미 제작 가능한 상태다.
- `wepoll-panic`은 주간 심리/참여 차트용 핵심 시계열이 2026-04-05까지는 안정적으로 정리돼 있다.
- 다만 두 프로젝트를 연결하는 "이벤트 이후 반응", "4/12까지 누적된 후속 게시물 반영", "이번 주 vs 평소 같은 요일 평균" 계열은 아직 2026-04-12 데이터 확보 이후 재산출이 맞다.

## 1. `wepoll-samsung`

### 지금 바로 가져와도 되는 파일

이 파일들은 이벤트 결과 자체를 설명하는 데 필요한 핵심 자산이다.

- `../wepoll-samsung/output/event_analysis/consensus.csv`
  - 차트 용도: 위폴 vs 증권사 컨센서스 vs 실제값
- `../wepoll-samsung/output/event_analysis/level_summary.csv`
  - 차트 용도: 레벨별 참여 비중, 레벨별 정확도
- `../wepoll-samsung/output/event_analysis/staff.csv`
  - 차트 용도: 슈친 직원 dot plot
- `../wepoll-samsung/output/event_analysis/post_timing/overall.csv`
  - 차트 용도: 위폴은 업무시간형 커뮤니티인가
- `../wepoll-samsung/output/event_analysis/post_timing/weekday_avg.csv`
  - 차트 용도: 평소 같은 요일 평균 baseline
- `../wepoll-samsung/output/event_analysis/member_image_baseline/mention_summary.csv`
  - 차트 용도: 멤버 호명량 baseline
- `../wepoll-samsung/output/event_analysis/member_image_baseline/sentiment.csv`
  - 차트 용도: 멤버별 감성 분포 baseline
- `../wepoll-samsung/output/event_analysis/member_image_baseline/post_type.csv`
  - 차트 용도: 멤버별 게시물 타입 baseline
- `../wepoll-samsung/output/event_analysis/member_image_baseline/monthly.csv`
  - 차트 용도: 멤버 언급 추이 baseline
- `../wepoll-samsung/output/event_analysis/fightin_words/summary.csv`
  - 차트 용도: 멤버별 baseline 키워드 비교

### 2026-04-12 데이터 확보 후 가져오는 게 맞는 파일

이 파일들은 현재도 산출물은 있지만, 공식 피겨로 쓰기엔 아직 이르다.

- `../wepoll-samsung/output/event_analysis/fightin_words_prepost/2026-04-06_pre14_post7/summary.csv`
- `../wepoll-samsung/output/event_analysis/fightin_words_prepost/2026-04-06_pre14_post7/prepost_슈카.csv`
- `../wepoll-samsung/output/event_analysis/fightin_words_prepost/2026-04-06_pre14_post7/prepost_알상무.csv`
- `../wepoll-samsung/output/event_analysis/fightin_words_prepost/2026-04-06_pre14_post7/prepost_니니.csv`

사유:

- 현재 pre/post 보고서에는 `post 게시물 수: 40`, `post 호명 게시물 수: 5`라고 적혀 있다.
- 문서 자체도 `현재 데이터 시점에 따라 post 구간 표본이 매우 작을 수 있다`고 경고한다.
- 같은 문서에서 `4/12까지 데이터가 들어오면 같은 명령으로 바로 재실행`한다고 명시돼 있다.

즉 이 묶음은 **지금은 시범 실행 결과**, 2026-04-12 데이터 확보 후에는 **정식 시각화 후보**다.

### 실무 권장 인입 순서

1. `consensus.csv`
2. `level_summary.csv`
3. `staff.csv`
4. `post_timing/overall.csv`
5. `post_timing/weekday_avg.csv`
6. `member_image_baseline/*` 중 핵심 baseline CSV
7. `fightin_words_prepost/*`는 2026-04-12 이후 재산출본으로 교체

## 2. `wepoll-panic`

### 지금 바로 가져와도 되는 파일

현재 기준으로 안정적인 주간/시계열 차트 재가공에 적합한 파일들이다.

- `../wepoll-panic/output/yearly_hybrid_batch_v4/psychology_participation_postcount_timeseries_append_2026-04-05.csv`
  - 차트 용도: 일별 심리/참여/게시물 수 시계열
- `../wepoll-panic/output/yearly_hybrid_batch_v4/anchor_quadrant_v10r_marketblend_labels_append_2026-04-05.csv`
  - 차트 용도: 일별 상태 라벨 및 주요 포인트 요약
- `../wepoll-panic/output/yearly_hybrid_batch_v4/weekly_bubble_points_2026-02-23_2026-04-05.csv`
  - 차트 용도: 주차별 bubble/constellation 계열 차트

참고:

- 관련 보고서는 분석 기간을 `2026-02-23 ~ 2026-04-05`로 명시한다.
- 상위 폴더의 최신 append 산출물 수정 시각도 2026-04-06이다.

### 2026-04-12 데이터 확보 후 가져오는 게 맞는 파일

이벤트 반응을 `wepoll-samsung`과 엮어 보여주려면 아래 항목은 최신화 후 가져오는 편이 맞다.

- `../wepoll-panic/output/yearly_hybrid_batch_v4/yearly_merged_posts_greed_v8_full.csv` 기반 재산출 결과
- `psychology_participation_postcount_timeseries_append_2026-04-12.csv` 또는 그에 준하는 최신 파일
- `weekly_bubble_points_..._2026-04-12.csv` 또는 그에 준하는 최신 파일
- `anchor_quadrant_..._append_2026-04-12.csv` 또는 그에 준하는 최신 파일

사유:

- `wepoll-samsung`의 월요일 체크리스트는 `../wepoll-panic/output/yearly_hybrid_batch_v4/yearly_merged_posts_greed_v8_full.csv`의 `created_at` 최대값이 최소 2026-04-12 이후까지 가야 한다고 적고 있다.
- 같은 문서에서 `2026-04-06 ~ 2026-04-12` 구간 게시물 수가 비어 있지 않아야 한다고 명시한다.
- 따라서 이벤트 이후 커뮤니티 활성화 여부나 평소 같은 요일 평균 대비 초과 활동량을 말하려면, 2026-04-12까지 포함한 최신 append 버전이 필요하다.

### 실무 권장 인입 순서

1. `psychology_participation_postcount_timeseries_append_2026-04-05.csv`
2. `weekly_bubble_points_2026-02-23_2026-04-05.csv`
3. `anchor_quadrant_v10r_marketblend_labels_append_2026-04-05.csv`
4. 2026-04-12 이후 최신 append 버전으로 교체

## 3. What We Can Build Now

지금 당장 Datawrapper 작업을 시작해도 되는 차트:

- 위폴 vs 컨센서스 vs 실제값
- 레벨별 참여 비중
- 레벨별 정확도 비율
- 슈친 직원 dot plot
- 위폴 baseline 시간대/요일 분포
- 위폴 멤버 이미지 baseline
- 위폴 panic 주간 심리/참여 시계열
- 위폴 panic 주차별 bubble chart

## 4. What Should Wait For 2026-04-12 Data

2026-04-12 데이터 확보 후 확정하는 차트:

- 이벤트 주간 활동량 vs 평소 같은 요일 평균
- 이벤트 이후 post 구간이 충분히 쌓인 Fightin' Words pre/post
- 슈카 이미지 변화 확정판
- 이벤트 직후 위폴 panic 시계열 업데이트판
- `wepoll-samsung`과 `wepoll-panic`를 연결한 cross-project 스토리
