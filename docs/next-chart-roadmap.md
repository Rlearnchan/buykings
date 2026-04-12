# Next Chart Roadmap

기준일: 2026-04-12

이 문서는 현재까지 확정된 차트 스타일과, 다음으로 제작할 그래프 후보를 한 번에 정리한 실행 메모다.

## Current Baseline

- Datawrapper -> PNG export -> Notion draft 파이프라인은 이미 동작한다.
- `wepoll-samsung` first batch 4개는 실제 publish와 PNG export, Notion 반영까지 완료됐다.
- 앞으로의 기본 규칙은 아래와 같다.
  - 제목은 짧고 건조하게 쓴다.
  - 단위는 가능하면 축이나 값 레이블에서 해결한다.
  - source는 짧게 유지한다.
  - 값 레이블이 핵심인 비교 차트는 dot/scatter보다 column chart 대체안을 먼저 본다.
  - 축 범위와 custom ticks는 메시지가 가장 잘 읽히는 범위로 고정한다.
  - 핵심 항목 1개만 강조색으로 잡고 나머지는 중립색으로 둔다.
  - intro 한 줄은 표본 범위나 집계 정의처럼 해석 전에 알아야 할 사실만 넣는다.

## Immediate Cleanup

- `wepoll-samsung` first batch에서 웹 UI로 직접 수정한 데이터 행을 prepared CSV 또는 별도 prepared CSV로 되돌려 적어 재현 가능성을 확보한다.
- current publish 상태와 local spec이 어긋나지 않도록 `consensus`, `staff` 차트용 prepared CSV를 확정한다.
- 최신 publish URL과 최신 PNG를 기준으로 Notion 드래프트를 한 번 더 최종 점검한다.

## Next Charts: Wepoll Samsung

### Tier 1

- `2026-04-11_post_timing_overall.csv`
  - 목표: 이벤트 시점 전후 전체 게시 활동 시간대 분포
  - 권장 차트: line 또는 column
  - 포인트: 업무시간형 baseline인지, 특정 시간 몰림이 있는지

- `2026-04-11_post_timing_weekday_avg.csv`
  - 목표: 평소 같은 요일 평균과 이벤트일 비교
  - 권장 차트: dual line 또는 grouped column
  - 포인트: 이벤트 효과가 평소 대비 얼마나 이례적인지

- `2026-04-11_member_image_mention_summary.csv`
  - 목표: 멤버별 호명량 비교
  - 권장 차트: horizontal bar
  - 포인트: 특정 멤버 쏠림 여부

### Tier 2

- `member semantic periods`
  - 목표: `2025 / 2026 / 이벤트주간` 기준 주요 단어 약 50개의 Word2Vec PCA와 멤버별 similar 5개 표
  - 권장 산출물: SVG scatter + Markdown table note
  - 현재 자산:
    - `exports/wepoll-samsung/semantic-periods/member-word2vec-period-pca.svg`
    - `projects/wepoll-samsung/notes/member-word2vec-periods.md`
  - 포인트: 감성 비중 차트보다 narrative가 풍부하고, 세 시기 간 맥락 변화를 더 잘 보여준다

- `wepoll weekly datawrapper`
  - 목표: 주간 운영용 timeseries + bubble chart를 같은 `chart_id`로 반복 갱신
  - 현재 자산:
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_recent6w.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_timeseries_state_ranges_recent6w.csv`
    - `projects/wepoll-panic/prepared/dw_weekly_bubble_latest_week.csv`
    - `projects/wepoll-panic/charts/weekly-timeseries-datawrapper.json`
    - `projects/wepoll-panic/charts/weekly-bubble-datawrapper.json`
  - 포인트: 삼성 개별 리포트보다 반복 운영 가치가 더 크다

- `2026-04-11_member_image_post_type.csv`
  - 목표: 멤버별 게시물 타입 구성
  - 상태: 현재는 제외
  - 포인트: 언급량/동의어 처리와 함께 다시 볼 여지는 있으나, 현 시점 우선순위는 낮다

- `2026-04-11_member_image_monthly.csv`
  - 목표: 멤버 언급 추이
  - 권장 차트: line
  - 포인트: 기간 길이가 길면 주요 멤버만 남기고 나머지는 묶는 방안 검토

### Deferred

- `2026-04-11_fightin_words_summary.csv`
  - 2026-04-12 이후 재산출본과 함께 보는 편이 안전하다.
  - 현재는 시범 메모 수준으로 두고, final narrative에는 바로 쓰지 않는다.

## Next Charts: Wepoll Panic

### Tier 1

- `2026-04-11_psychology_participation_postcount_timeseries_append_2026-04-05.csv`
  - 목표: 일별 심리/참여/게시물 수 시계열 템플릿 확정
  - 권장 차트: dual-axis는 피하고 small multiples 또는 separate line chart 우선

- `2026-04-11_weekly_bubble_points_2026-02-23_2026-04-05.csv`
  - 목표: 주차별 bubble chart 템플릿 확정
  - 권장 차트: bubble
  - 포인트: 방송/PPT 가독성을 위해 label 전략을 먼저 정해야 한다

- `2026-04-11_anchor_quadrant_v10r_marketblend_labels_append_2026-04-05.csv`
  - 목표: 상태 라벨 + 주요 날짜 포인트 시각화
  - 권장 차트: scatter/quadrant
  - 포인트: reference image 스타일과 가장 가까운 템플릿 후보

## Recommended Order

1. `wepoll-samsung` first batch 재현성 정리
2. `post_timing_overall` + `post_timing_weekday_avg`
3. `wepoll weekly datawrapper`
4. `member semantic periods`
5. `wepoll-panic` quadrant / bubble template

## Deliverable Rule

새 차트를 하나 추가할 때마다 아래 4종이 함께 남아야 한다.

- `incoming/` 원본 CSV
- `prepared/` 차트 전용 CSV
- `charts/` JSON spec
- `exports/` PNG

가능하면 같은 턴에서 Notion draft spec까지 같이 갱신한다.
