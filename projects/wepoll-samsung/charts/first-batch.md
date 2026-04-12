# First Batch

기준일: 2026-04-11

파이프라인 점검용으로 가장 먼저 Datawrapper에 올려볼 prepared CSV 목록이다.

## Ready Now

- `prepared/dw_consensus_vs_actual.csv`
  - recommended chart: dot plot 또는 horizontal bar chart
  - message: 위폴도 실제보다 보수적이었지만, 컨센서스보다는 실제값에 더 가까웠다
- `prepared/dw_level_participation.csv`
  - recommended chart: column chart
  - message: 이벤트 참여는 사실상 레벨 1이 주도했다
- `prepared/dw_level_accuracy.csv`
  - recommended chart: column chart
  - message: 중간 레벨 구간의 정확도 비율이 높아 보이지만 표본은 작다
- `prepared/dw_staff_dotplot.csv`
  - recommended chart: dot plot
  - message: 직원들도 대체로 실제보다 낮게 봤고, 에이전트가 가장 실제값에 가까웠다

## Why This Batch

- 메시지가 명확하다
- 원본 CSV 구조가 이미 안정적이다
- Datawrapper API 테스트 대상으로도 적합하다
- 향후 스타일 템플릿을 만들기 좋은 차트 유형들이다

## Publishing Log

- consensus vs actual
  - chart id: `l2iDU`
  - public url: `https://datawrapper.dwcdn.net/l2iDU/4/`
  - current style note: value labels were prioritized, so the earlier dot plot concept was replaced with a column-chart presentation
- level participation
  - chart id: `zcSSe`
  - public url: `https://datawrapper.dwcdn.net/zcSSe/4/`
  - current style note: level 1 is highlighted and sample scope is shown in the intro line
- level accuracy
  - chart id: `QnKDM`
  - public url: `https://datawrapper.dwcdn.net/QnKDM/4/`
  - current style note: level 5-9 is highlighted and the 1조 기준 is explained in the note
- staff dot plot
  - chart id: `StnVb`
  - public url: `https://datawrapper.dwcdn.net/StnVb/6/`
  - current style note: value labels were prioritized, so the earlier dot plot concept was replaced with a column-chart presentation
