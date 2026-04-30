# Dashboard Quality Review

Autopark의 날짜별 Notion 문서는 발행 전에 `review_dashboard_quality.py`를 통과시키는 것을 목표로 한다. 리뷰는 0421 Notion 포맷 체크리스트와 PPT 3개 방송서사 분석에서 나온 규칙을 나눠 본다.

## Command

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/review_dashboard_quality.py --date 2026-04-29
```

기본 입력은 `projects/autopark/runtime/notion/YYYY-MM-DD/YY.MM.DD.md`이고, 결과는 아래에 저장된다.

- `projects/autopark/runtime/reviews/YYYY-MM-DD/dashboard-quality.md`
- `projects/autopark/runtime/reviews/YYYY-MM-DD/dashboard-quality.json`

`gate`가 `needs_revision`이면 exit code 1을 반환한다. 발행 전 파이프라인에서는 이 값을 품질 게이트로 쓸 수 있다.

## Format Checks

- 페이지 제목이 날짜만 있는지 확인한다.
- `최종 수정 일시`, `수집 구간`이 분 단위 KST로 들어갔는지 확인한다.
- `주요 뉴스 요약`, `추천 스토리라인`, `자료 수집`, `시장은 지금`, `오늘의 이모저모`, `실적/특징주` 섹션을 확인한다.
- 추천 스토리라인 3개, quote block, 선정 이유, 슬라이드 구성 슬롯을 확인한다.
- 원문 URL 노출, `볼 포인트` 같은 래퍼성 불릿 라벨을 감지한다.

## Content Checks

- 고정 시장 루틴이 PPT 순서에 맞게 들어갔는지 확인한다.
  - 주요 지수 흐름
  - S&P500 히트맵
  - 러셀 2000 히트맵
  - 10년물
  - WTI, 브렌트
  - DXY, 원달러
  - 비트코인
  - 공포탐욕지수
  - 실적 캘린더
  - 경제지표 캘린더
- 오늘의 메인 thesis가 명시됐는지 확인한다.
- 에너지/OPEC/이란/호르무즈가 메인일 때 생산량, 쿼터, 수송 병목, 에너지 섹터/종목, EIA 이벤트 같은 증거 장표를 요구한다.
- 스토리라인 내부 시각 자료, 텍스트-only 정리 슬라이드 후보, 자료 간 연결 지시를 확인한다.
- 실적/특징주가 단순 종목 나열이 아니라 상위 테마 증명 구조인지 확인한다.

## Current 04.29 Result

현재 04.29 문서 기준 결과는 `format score 100`, `content score 76`, `gate needs_revision`이다.

주요 지적은 두 가지다.

- 고정 시장 루틴에서 주요 지수 흐름, S&P500 히트맵, 러셀 2000 히트맵, 공포탐욕지수, 실적 캘린더가 빠져 있다.
- 실적/특징주가 아직 상위 테마를 증명하는 구조로 묶이지 않았다.
