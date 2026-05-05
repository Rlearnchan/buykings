# Autopark 2차 완성 기준 - 2026-05-05

## 기준점

2026-05-05 현 시점을 Autopark compact dashboard의 "2차 완성" 상태로 고정한다.

1차 완성은 `projects/autopark/docs/handoffs/2026-05-04-codex-handoff.md`에 남긴 MVP 기준이며, 2차 완성은 그 위에 수집 소스, 미디어 포커스, 특징주, 마이크로카피 렌더 품질을 보강한 상태다.

## 최신 발행 확인

- Notion title: `26.05.05`
- Latest URL: `https://www.notion.so/26-05-05-357468fb878d81fd91c7c905563173a9`
- Quality gate: pass, `100/100/100`, finding `0`
- 발행 위치: 공개 대시보드의 `오늘의 자료` 아래

## 2차 완성에서 고정할 것

- Compact dashboard format은 유지한다.
- 상단 진행자용 요약은 한 줄 핵심 문구 중심으로 둔다.
- `## 1. 시장은 지금`은 시장 차트/테이블 중심이며, 차트별 `요약:`/`내용:`은 넣지 않는다.
- 시장 카드 하위 제목은 `(A)`, `(B)` 형식으로 표기한다.
- FedWatch는 하나의 `FedWatch` 소제목 아래 단기/장기 표를 순서대로 둔다.
- 경제일정은 `오늘의 경제지표` 아래 미국/글로벌 표를 순서대로 둔다.
- `## 2. 미디어 포커스`는 외부 수집 자료 창고로 유지한다.
- 미디어 포커스 번호는 `(1)`부터 `(40)` 형식으로 둔다.
- 미디어 포커스에는 `점수:`를 노출하지 않는다.
- 미디어 포커스의 `주요 내용`은 1~3개 불릿으로 렌더한다.
- 마이크로카피가 한 항목 안에 여러 문장을 넣어도 렌더러가 문장/줄바꿈 기준으로 최대 3개 불릿으로 나눈다.
- 긴 세미콜론 구문은 조건부로 불릿 분리한다. 짧은 세미콜론 표현은 유지한다.
- `## 3. 실적/특징주`는 실적 캘린더와 Yahoo trending top 10 기반 특징주만 보여준다.
- 특징주는 `### 기업명 (티커)` 형식, Finviz 출처, 캡처 시점, 차트, 선택적 주요 내용으로 구성한다.

## 최근 구현 요약

- Yahoo trending stocks collector 추가.
- Yahoo trending 기본 수집 상한을 10개로 조정.
- Yahoo 파서는 `data-testid="data-table-v2-row"`와 `data-testid-cell` 기반으로 테이블 섹션을 우선 읽는다.
- Finviz feature stock capture가 Yahoo tickers file을 입력으로 받을 수 있게 수정.
- Feature stock microcopy helper 추가.
- Dashboard renderer가 feature stock microcopy를 읽어 `## 3. 실적/특징주`에 반영한다.
- Dashboard microcopy prompt가 미디어 포커스 `content_bullets`를 문장별 array item으로 요구한다.
- Renderer가 미디어 포커스 주요 내용을 줄바꿈/문장 경계/긴 세미콜론 기준으로 1~3개 불릿으로 분리한다.
- Docker retrospective automation은 daily path에서 분리하고 manual operation 문서로 남겼다.

## 남은 개선 후보

- 스토리라인의 괄호/문장 완결성 품질 보강.
- 미디어 포커스의 source-title mismatch 정리. 예: BizToc URL과 제목이 어긋나는 후보.
- Accuray 같은 실적 preview는 미디어 포커스보다 실적/특징주 쪽으로 분류하는 규칙 검토.
- Dashboard microcopy를 새로 호출하면 미디어 포커스 2~3불릿 비율을 더 높일 수 있다.
- Feature stock capture는 headed Chrome/CDP 환경에서 안정적이므로 자동화 환경에서도 같은 경로를 쓰는지 계속 확인한다.

## Stage 주의

커밋할 때는 Autopark 2차 완성 관련 코드와 문서만 선별한다.

제외할 것:

- `projects/wepoll-panic/**`
- 런타임 Notion/스크린샷/리뷰 산출물
- 2026-05-04 source audit/sourcebook 임시 산출물
- 사용자가 명시하지 않은 chart JSON/PPT/PDF/RTF

