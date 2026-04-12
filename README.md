# Datawrapper Visualization Workspace

이 저장소는 여러 분석 프로젝트의 **최종 CSV를 받아, Datawrapper 기반 시각화만 전문적으로 제작하는 작업 공간**이다.

핵심 목적은 세 가지다.

1. 다른 분석 폴더에서 정리된 최종 CSV를 받아온다.
2. Datawrapper에 바로 넣기 좋은 형태로 데이터를 다듬는다.
3. 기존 차트의 형식, 글꼴, 문장 톤, 색상 체계를 최대한 유지해 리서치 피겨처럼 일관되게 산출한다.

장기적으로 프로젝트는 계속 추가될 수 있다. 현재는 아래 두 축으로 시작한다.

- `wepoll-panic`: 위폴 주간 데이터 분석용 시각화
- `wepoll-samsung`: 삼성 이벤트 데이터 분석용 시각화

## Workspace Structure

```text
.
|-- README.md
|-- docs/
|   |-- datawrapper-notes.md
|   `-- style-guide.md
|-- exports/
|-- datawrapper/
|-- templates/
|   `-- chart-spec-template.md
|-- projects/
|   |-- wepoll-panic/
|   |   |-- incoming/
|   |   |-- prepared/
|   |   |-- charts/
|   |   `-- notes/
|   `-- wepoll-samsung/
|       |-- incoming/
|       |-- prepared/
|       |-- charts/
|       `-- notes/
`-- logo/
```

## Folder Roles

### `projects/<project>/incoming`

- 다른 분석 저장소에서 넘어온 최종 CSV 원본 보관
- 가능하면 여기서는 원본을 수정하지 않는다
- 파일명 예시: `2026-04-11_level_summary_final.csv`

### `projects/<project>/prepared`

- Datawrapper 업로드용 CSV 저장
- 원칙은 **차트 1개당 CSV 1개**
- 파일명 예시:
  - `dw_level_participation.csv`
  - `dw_level_accuracy.csv`
  - `dw_consensus_vs_actual.csv`

### `projects/<project>/charts`

- 차트별 작업 메모
- 최종 제목, 부제, 주석, source 문구, 색상 메모 기록
- 필요하면 발행된 Datawrapper chart ID도 함께 적는다

### `projects/<project>/notes`

- 프로젝트 메시지 정리
- 어떤 차트를 왜 만드는지, 발표 문맥에서 어떤 순서로 쓸지 기록

### `docs`

- 프로젝트 공통 운영 규칙
- 스타일 가이드
- Datawrapper 사용 메모

### `templates`

- 새 프로젝트나 새 차트 시작 시 복사해서 쓰는 템플릿

### `exports`

- 외부 전달용 PNG, PDF, SVG, 캡션 문안 등을 모으는 공간
- Free 플랜에서는 PNG 중심으로 운영하는 것을 기본값으로 본다
- `wepoll-panic/weekly`는 대표 최신본과 날짜별 스냅샷을 함께 유지한다

## Standard Workflow

1. 분석 저장소에서 최종 CSV를 `incoming/`에 복사
2. 메시지 단위로 CSV를 쪼개거나 가공해서 `prepared/`에 저장
3. `templates/chart-spec-template.md`를 복사해 차트 스펙 작성
4. Datawrapper에서 차트 제작
5. 제목, 부제, 주석, source, 색상 규칙을 `charts/`에 기록
6. 최종 산출물을 `exports/`에 정리

## Datawrapper Operating Principles

- 이 저장소에서는 분석보다 시각화 완성도를 우선한다.
- 같은 성격의 차트는 가능하면 같은 축 범위, 색상 체계, 숫자 표기 방식을 쓴다.
- 글꼴, 범례 위치, 주석 문체, source 표기 방식을 최대한 반복 사용한다.
- 원본 CSV가 차트 친화적이지 않다면 `prepared/`에서 별도 가공본을 만든다.
- 대시보드보다도 먼저, 발표 슬라이드와 리서치 문서에 바로 붙일 수 있는 단일 피겨 품질을 목표로 한다.

## Current Project Scope

### `wepoll-panic`

- 위폴 주간 흐름을 반복적으로 시각화하는 트랙
- 주차별로 비슷한 포맷이 반복될 가능성이 높으므로 템플릿화 우선

### `wepoll-samsung`

- 삼성 이벤트 분석 결과를 시각화하는 트랙
- 대표 차트 후보:
  - 위폴 vs 컨센서스 vs 실제값
  - 레벨별 참여 비중
  - 레벨별 정확도
  - 직원 예측 dot plot
  - 커뮤니티 활동 시간대 baseline

## Datawrapper Plan Check

Datawrapper 공식 문서를 2026-04-11 기준으로 확인한 메모:

- Free 플랜은 차트/맵/테이블의 게시와 PNG export를 제한 없이 제공한다고 안내한다.
- API 문서는 별도 developer portal로 공개돼 있어 API 사용 자체는 공식 지원되는 기능으로 보인다.
- Terms of Service에는 개인뿐 아니라 조직, 회사, 기관을 대신한 사용을 전제로 한 조항이 포함되어 있다.
- 다만 Free 플랜에서 브랜딩 제거, 고급 커스터마이징, 추가 export 옵션은 제한될 수 있다.

상업적 활용 관련 판단:

- 현재 확인한 공식 문서에서는 Free 플랜 사용자가 유튜브 방송 등 상업적 맥락에서 차트를 게시하는 것을 일반적으로 금지하는 조항은 찾지 못했다.
- 다만 사용 데이터의 재배포 권리, 출처 표기, 저작권 준수 책임은 사용자에게 있다.
- 약관과 요금제는 바뀔 수 있으므로 실제 방송 투입 직전에는 한 번 더 확인하는 것이 안전하다.

자세한 메모와 링크는 [docs/datawrapper-notes.md](/Users/bae/Documents/code/buykings/docs/datawrapper-notes.md) 참고.

## Current Progress

2026-04-11 기준으로 현재까지 완료된 작업은 아래와 같다.

- 저장소 구조를 `incoming / prepared / charts / notes` 중심으로 정리
- 프로젝트 이름을 상위 작업 폴더와 맞춰 `wepoll-panic`, `wepoll-samsung`으로 통일
- Datawrapper free 플랜, API, 상업적 활용 관련 공식 문서 검토
- 상위 분석 저장소에서 1차 원본 CSV를 `incoming/`으로 복사
- `wepoll-samsung` 핵심 차트 4종용 prepared CSV 생성

현재 바로 Datawrapper에 올려볼 수 있는 prepared 파일:

- `projects/wepoll-samsung/prepared/dw_consensus_vs_actual.csv`
- `projects/wepoll-samsung/prepared/dw_level_participation.csv`
- `projects/wepoll-samsung/prepared/dw_level_accuracy.csv`
- `projects/wepoll-samsung/prepared/dw_staff_dotplot.csv`

참고 문서:

- 인입 계획: [docs/source-ingest-plan.md](/Users/bae/Documents/code/buykings/docs/source-ingest-plan.md)
- Datawrapper API 메모: [docs/api-next-steps.md](/Users/bae/Documents/code/buykings/docs/api-next-steps.md)
- 첫 실행 런북: [docs/first-run-playbook.md](/Users/bae/Documents/code/buykings/docs/first-run-playbook.md)

## Future Automation

장기적으로는 이 저장소를 아래 흐름으로 확장할 수 있다.

1. 상위 분석 저장소에서 최종 CSV 수신
2. `prepared/`용 차트별 CSV 자동 생성
3. Datawrapper API로 차트 생성, 데이터 업로드, publish
4. Notion API로 리포트 초안 페이지 생성
5. 차트 이미지와 핵심 문장을 자동 삽입
6. 사람이 최종 검수 후 발표/문서에 사용

즉 목표는 "분석 자동화"가 아니라, **초안 보고서와 피겨 생산 속도를 크게 높이는 시각화 파이프라인**이다.

## Notion Possibility

Notion API가 있으면 보고서 초안 생성도 충분히 가능하다.

가능한 것:

- 페이지 생성
- 문단, 제목, 리스트, 표 등 블록 추가
- 외부 URL 기반 이미지 삽입
- API 업로드 또는 외부 파일 기반 이미지/파일 첨부
- chart caption, source, note를 포함한 보고서 초안 자동 작성

실무적으로 가장 자연스러운 구조:

1. `prepared/` CSV로 Datawrapper 차트 생성
2. publish URL 또는 export 이미지 확보
3. Notion 페이지 생성
4. 섹션 제목, 핵심 문장, 차트 이미지, source, note를 순서대로 append

주의할 점:

- 최종 문안과 레이아웃은 사람이 검수하는 전제를 유지하는 것이 좋다.
- 외부 이미지 URL 삽입과 Notion 내부 파일 업로드는 운영 방식이 조금 다르다.
- Datawrapper PNG export와 Notion 첨부 방식은 실제 계정/플랜에 맞춰 한 번 테스트해야 한다.

관련 메모는 [docs/notion-report-pipeline.md](/Users/bae/Documents/code/buykings/docs/notion-report-pipeline.md) 참고.

## Next Recommended Steps

1. `wepoll-samsung` first batch에서 웹 UI 수정을 local spec / prepared CSV로 되돌려 적어 재현 가능성을 확보한다.
2. `wepoll-samsung`의 `post_timing`, `member_image` 계열 차트를 다음 배치로 만든다.
3. `wepoll-panic`의 `timeseries`, `quadrant`, `bubble` 템플릿을 확정한다.
4. 새 차트는 가능하면 같은 턴에서 `publish -> PNG export -> Notion draft`까지 같이 갱신한다.

자세한 실행 우선순위는 [docs/next-chart-roadmap.md](/Users/bae/Documents/code/buykings/docs/next-chart-roadmap.md) 참고.

## Resume Point

기존 스레드가 끊겨도 여기서 바로 재개할 수 있도록 현재 기준점을 적어둔다.

- 현재 작업 기준일은 `2026-04-12`
- `Datawrapper -> PNG export -> Notion draft` 파이프라인은 실동작 확인이 끝났다
- `wepoll-samsung` first batch 4개는 publish / PNG / Notion 반영까지 완료됐다
- 현재 다음 큰 단계는 `wepoll-samsung` 남은 incoming CSV와 `wepoll-panic` 템플릿 차트를 추가 제작하는 것이다

## API Connection Track

이 저장소에서 다음으로 붙일 자동화는 아래 두 축이다.

### Datawrapper API

- 목적: prepared CSV에서 chart create -> data upload -> metadata update -> publish를 반복 가능하게 만들기
- 시작 대상: `wepoll-samsung` first batch 중 `consensus`, `level participation`
- 작업 메모: [docs/api-next-steps.md](/Users/bae/Documents/code/buykings/docs/api-next-steps.md)

### Notion Draft API

- 목적: 발행된 chart URL 또는 export 이미지를 바탕으로 초안 보고서 페이지 자동 생성
- 시작 대상: `wepoll-samsung` first batch 3~4개를 묶은 보고서 초안
- 작업 메모: [docs/notion-report-pipeline.md](/Users/bae/Documents/code/buykings/docs/notion-report-pipeline.md)

실무적으로는 먼저 Datawrapper chart publish가 안정화돼야 Notion 초안 자동화도 자연스럽게 이어진다.
