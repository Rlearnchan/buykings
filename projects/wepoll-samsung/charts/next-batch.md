# Next Batch

기준일: 2026-04-12

first batch 이후 추가 제작할 차트와 진행 상태를 기록한다.

## Published Now

- post timing weekday average
  - chart id: `SJcxa`
  - public url: `https://datawrapper.dwcdn.net/SJcxa/1/`
  - PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/next-batch/post-timing-weekday-avg.png`
  - style note: 평일은 중립색, 최고 요일은 강조색, 주말은 회색으로 처리
  - takeaway: 게시물 활동은 평일, 특히 목-금 구간이 높고 주말에는 크게 줄어든다

- post timing weekday split
  - chart id: `EQKOK`
  - public url: `https://datawrapper.dwcdn.net/EQKOK/1/`
  - PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/next-batch/post-timing-weekday-yearsplit.png`
  - style note: x축은 월~일, 시리즈는 `2025년 / 2026년 / 이벤트 주간`, 이벤트 주간은 오늘 데이터 제외 임시판
  - takeaway: 2026년 평일 게시물 수는 2025년보다 전반적으로 높고, 이벤트 주간은 화~수 구간이 특히 강하다

- member image mention posts
  - status: dropped
  - reason: 동의어 처리 완성도 이슈로 현재 단계에서는 대표 차트로 쓰기 어렵다

- member image post type share
  - status: dropped
  - reason: 현재 narrative에서 우선순위가 낮고, 대표 메시지 차트로는 임팩트가 약하다

- member semantic periods
  - status: draft ready
  - asset: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/member-word2vec-period-pca.svg`
  - note: `2025 / 2026 / 이벤트주간` 기준 주요 단어 약 50개 PCA와 멤버별 similar 5개 표를 생성했다
  - report: `/Users/bae/Documents/code/buykings/projects/wepoll-samsung/notes/member-word2vec-periods.md`
  - review csv: `/Users/bae/Documents/code/buykings/projects/wepoll-samsung/prepared/dw_member_word2vec_candidate_dots.csv`
  - table csv: `/Users/bae/Documents/code/buykings/projects/wepoll-samsung/prepared/dw_member_word2vec_similar_table.csv`
  - follow-up: 토큰 정제 규칙은 추가 보정 여지가 있지만, 현재 버전은 placeholder/HTML 노이즈를 1차 정리한 초안이다

- member semantic scatter
  - 2025 chart id: `REjQy`
  - 2025 public url: `https://datawrapper.dwcdn.net/REjQy/1/`
  - 2025 PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/word2vec-2025.png`
  - 2026 chart id: `nI7xI`
  - 2026 public url: `https://datawrapper.dwcdn.net/nI7xI/1/`
  - 2026 PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/word2vec-2026.png`
  - 이벤트주간 chart id: `u08tZ`
  - 이벤트주간 public url: `https://datawrapper.dwcdn.net/u08tZ/1/`
  - 이벤트주간 PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/word2vec-eventweek.png`
  - note: 2025 / 2026 / 이벤트주간 3시기 scatter를 모두 발행했다

- member similar table
  - chart id: `Q1Xdw`
  - public url: `https://datawrapper.dwcdn.net/Q1Xdw/1/`
  - PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/word2vec-similar-table.png`
  - note: `2025 / 2026 / 이벤트주간` 전체 similar top 5를 한 표에 모았다
  - member split:
    - 슈카 `Y8oWd`
    - 알상무 `fgHQC`
    - 니니 `P1f7d`

- fightin words overall table
  - chart id: `6cmWE`
  - public url: `https://datawrapper.dwcdn.net/6cmWE/1/`
  - PNG: `/Users/bae/Documents/code/buykings/exports/wepoll-samsung/semantic-periods/fightin-words-overall-table.png`
  - note: 현 시점 전체 fightin words 표이며, 4/12 반영 후에는 `2025 / 2026 / 이벤트주간` 3분할로 재정리 예정

- fightin words member split
  - 슈카 `v8AfO`
  - 알상무 `HGf2C`
  - 니니 `gUxLZ`
  - note: 이벤트주간은 4/12 완전 반영 전 파이프라인 점검용 표

## Next Up

- `post_timing_overall`
  - chart보다 summary note 또는 report intro 근거값으로 쓰는 편이 자연스럽다
- `member semantic periods`
  - 현재 초안을 보고 최종 제목, anchor 색상, 표시 단어 50개 구성만 다듬으면 된다
- `wepoll-panic` 시계열/버블/사분면 템플릿
  - 삼성 차트 다음 배치보다 범용 템플릿 가치가 크다
