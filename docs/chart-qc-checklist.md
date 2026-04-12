# Chart QC Checklist

이 문서는 `buykings` 시각화 파이프라인에서 Datawrapper 차트를 검수할 때 반복해서 보는 체크리스트다.

## Copy

- 제목은 가운데 정렬을 기본으로 한다.
- 제목은 해석형 문장보다 기술형 문구를 우선한다.
- 축이나 값 레이블에서 단위가 충분히 보이면 제목에는 단위를 중복 표기하지 않는다.
- 해석이나 시사점은 차트 제목보다 리포트 본문에서 설명한다.
- 부제는 기준일, 표본 범위, 비교 기준만 짧게 적는다.
- note에는 표본이 작거나 해석상 주의가 필요한 점을 분리해 적는다.

## Layout

- 차트 폭은 차트 종류에 따라 다르게 export한다.
- dot plot은 지나치게 가로로 길어지지 않게 narrower export를 우선한다.
- column chart는 막대가 충분히 읽히되 제목과 축이 작아지지 않는 폭을 쓴다.
- 값 레이블이 핵심인 비교 차트는 dot/scatter보다 column chart 대체안을 먼저 검토한다.
- 긴 제목, 부제, footer가 plot 영역을 과하게 잡아먹지 않는지 본다.

## Typography

- 무료 테마에서는 `Datawrapper`(Roboto)와 `Datawrapper (2012)`(Helvetica)를 우선 비교한다.
- 모바일/PPT 가독성이 중요하면 `Datawrapper (high contrast)`도 별도 후보로 본다.
- 프로젝트 전체에서 한 가지 테마를 우선 고정한다.
- 로고, 커스텀 폰트, 세밀한 브랜드 테마는 Custom/Enterprise 전용 여부를 먼저 확인한다.

## Axes And Numbers

- 축 숫자에는 단위가 바로 읽히게 `%`, `조` 같은 표기를 붙인다.
- participation과 accuracy 계열은 퍼센트 축인지 한눈에 보여야 한다.
- 축 숫자와 범주 라벨은 좁은 화면에서도 읽히는지 PNG 기준으로 확인한다.
- 개별 축 폰트 bold 제어가 어려우면 테마 대비와 export 폭을 먼저 조정한다.
- 숫자 반올림 규칙은 프로젝트 전체에서 통일한다.
- 0에 가까운 미세 범주가 있으면 유지할지, note로만 넘길지 판단한다.
- column chart는 값 레이블을 기본값으로 켜고 `outside` 배치를 우선한다.
- 축 범위와 눈금은 자동에 맡기지 말고 메시지가 읽히는 범위로 고정하는 편을 우선 검토한다.

## Visual Meaning

- 실제값, 기준값, 하이라이트 값은 색이나 기준선으로 반복적으로 구분한다.
- 메시지의 핵심 비교 대상은 같은 색으로 뭉개지지 않게 한다.
- staff 계열처럼 기준점이 중요한 차트는 실제값 참조점을 반드시 보이게 한다.
- 표본 수가 작은 집단은 note 또는 annotation으로 경고한다.
- 핵심 막대 1개만 강조색으로 잡고 나머지는 중립색으로 두는 방식이 방송용 슬라이드에서 읽기 쉽다.
- intro 한 줄은 표본 범위나 집계 정의처럼 해석 전에 알아야 할 사실만 넣는다.

## Output

- Datawrapper publish URL과 PNG export 경로를 모두 남긴다.
- Notion 초안은 이전 동명 드래프트를 정리한 뒤 최신본 1개만 남긴다.
- 최종 대외 공유 전에는 PNG를 기준으로 모바일/좁은 폭 가독성을 다시 본다.
- `show-values`만으로 부족하면 `visualize.valueLabels.enabled/show/placement`까지 함께 저장됐는지 확인한다.
- source 표기는 짧고 건조하게 유지하고, 가능하면 `Created with Datawrapper`와 함께 한 줄에 정리한다.
- 웹 UI에서 데이터 행을 직접 수정했다면 다음 배치 전에 prepared CSV나 spec에 그 변경을 반드시 되돌려 적어 재현 가능성을 확보한다.
- `get-the-data`는 기본 비활성화하고 footer에는 source와 `Created with Datawrapper`만 남긴다.
- export 파일은 버전명을 계속 늘리지 말고 대표 파일 하나를 overwrite하는 방식을 우선한다.

## Current Constraints

- 현재 플랜에서는 BuyKings 로고를 차트 우측 상단에 기본 삽입하는 기능을 쓸 수 없다.
- 공식 문서 기준 로고와 커스텀 폰트는 custom design theme에 포함되며, 이는 Custom/Enterprise 플랜 범위다.
- 따라서 현재는 footer attribution을 유지하고, 로고는 Notion 리포트나 별도 표지에서 보완하는 쪽이 현실적이다.
