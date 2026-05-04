# Autopark Workflow Report

이 문서는 Autopark가 새벽에 어떻게 자료를 모으고, 판단하고, Notion 대시보드로 발행하는지 설명한다. 목적은 두 가지다.

1. 사람이 읽고 현재 파이프라인을 빠르게 이해한다.
2. GPT나 이미지 모델에 넣어 작업 흐름도를 그릴 수 있는 구조화된 설명으로 쓴다.

## 1. 한 문장 요약

Autopark는 새벽 시장 자료를 자동으로 수집한 뒤, 시장 데이터와 뉴스/분석 자료를 나누어 정리하고, 여러 단계의 LLM 편집 회의를 거쳐 진행자용 compact Notion 대시보드를 발행하는 자동 편집국이다.

## 2. 운영 시간과 실행 방식

기본 목표는 한국 시각 아침 5시 발행이다.

- 메인 실행: `05:00 KST`
- 재시도: `05:20 KST`
- 실행 주체: Docker scheduler
- 브라우저: 호스트의 visible Chrome CDP 프로필을 Docker에서 제어
- 발행 정책: quality gate 통과 시 Notion publish

브라우저를 완전 headless로 숨기지 않는 이유는 Finviz, X, CNN Fear & Greed처럼 동적 렌더링과 로그인 유지, 봇 탐지에 민감한 사이트가 있기 때문이다. 현재 구조는 Wepoll과 비슷하게, 브라우저는 오래 켜진 상태로 두고 Docker가 명령을 보내는 방식에 가깝다.

## 3. 최종 산출물

Autopark가 매일 만드는 핵심 산출물은 다음과 같다.

- Notion 발행용 Markdown
- Notion 페이지
- 시장 차트 이미지와 Datawrapper 그래프
- 수집 원천 데이터
- 가공 데이터
- market radar 후보 목록
- evidence microcopy
- market focus brief
- editorial brief
- dashboard microcopy
- quality gate 리포트
- sourcebook 내부 장부

최종 Notion 페이지는 compact dashboard 형식을 유지한다. 내부 엔진은 깊게 돌아가지만, 독자가 보는 화면은 진행자가 바로 읽을 수 있는 큐시트와 자료 창고에 가깝다.

## 4. 전체 데이터 흐름

아래 흐름이 Autopark의 큰 줄기다.

```text
Docker scheduler
  -> browser/CDP health check
  -> source collection
  -> screenshots and chart capture
  -> Datawrapper update/export
  -> market radar
  -> evidence microcopy
  -> market focus brief
  -> editorial brief
  -> dashboard microcopy
  -> compact dashboard render
  -> quality gate
  -> Notion publish
  -> sourcebook
```

중요한 원칙은 LLM이 구조를 마음대로 바꾸지 않는다는 점이다. 자료 순서, 카드 번호, 섹션 구조, publish 포맷은 renderer와 local code가 소유한다. LLM은 판단과 짧은 문장 생성에만 참여한다.

## 5. 데이터 저장 위치

파이프라인 중간 산출물은 대략 아래 위치에 쌓인다.

| 구분 | 위치 | 역할 |
|---|---|---|
| Raw data | `projects/autopark/data/raw/YYYY-MM-DD/` | 수집 직후 원천 자료 |
| Processed data | `projects/autopark/data/processed/YYYY-MM-DD/` | radar, brief, microcopy 등 가공 자료 |
| Chart inputs | `projects/autopark/prepared/` | Datawrapper에 넣을 CSV |
| Chart specs | `projects/autopark/charts/` | Datawrapper chart id와 설정 |
| Image exports | `projects/autopark/exports/current/` | Notion/PPT에 쓸 최신 이미지 |
| Runtime | `projects/autopark/runtime/` | 로그, Notion Markdown, 리뷰 결과 |
| Sourcebook | `projects/autopark/docs/sourcebooks/` | 내부 장부와 handoff 문서 |

Git에는 코드, 테스트, 설정, 문서, 의도적으로 변경한 chart spec만 올린다. raw output, runtime output, PPT/PDF/RTF, 임시 스크린샷, API raw response는 기본적으로 커밋하지 않는다.

## 6. 데이터 소스 구조

Autopark의 소스는 크게 세 갈래다.

### 6.1 시장 데이터

시장 지도 역할을 하는 자료다. Notion의 `## 1. 시장은 지금` 섹션에 들어간다.

- 주요 지수 흐름
- S&P500 히트맵
- 러셀 2000 히트맵
- 10년물 국채금리
- WTI
- 브렌트
- 달러인덱스
- 원/달러 환율
- 비트코인
- CNN Fear & Greed
- FedWatch 단기/장기
- 오늘의 경제지표

이 섹션은 시장 상황을 보여주는 지도라서 `요약:`이나 `내용:`을 붙이지 않는다. 차트와 표 자체가 본문이다. 기준 시점은 가능하면 한국 시각으로 명확히 적는다.

### 6.2 Headline River

속보와 뉴스 헤드라인의 기본 강이다. “오늘 시장에서 무엇이 화제가 되었나”를 넓게 깐다.

우선순위는 다음과 같다.

1. Yahoo ticker RSS와 pre-flight agenda 확장
2. 공식 X 뉴스 계정
3. BizToc, Finviz fallback

Yahoo ticker RSS는 특정 ticker와 agenda에 연결된 뉴스 흐름을 보기 좋다. Finviz news는 헤드라인 baseline으로 유용하지만, 잡음이 많을 수 있어 우선순위는 낮다. BizToc은 키워드와 시장 관심을 훑는 보조 소스로 본다.

### 6.3 Analysis River

시장을 해석하는 자료의 강이다. 단순 뉴스보다 “방송에서 어떻게 읽을 것인가”에 더 가까운 자료다.

현재 고정한 분석 소스는 다음과 같다.

- Kobeissi Letter: 거시 지표, 시장 심리, 차트 기반 스토리
- Wall St Engine: 실적 일정, 실적 반응, 핵심 뉴스 요약
- Liz Ann Sonders: 노동, 물가, 선행지표, 섹터/ETF 흐름
- Charlie Bilello: 장기 데이터, 역사적 사이클, 비교 차트
- Nick Timiraos: FOMC, Fed 발언, 경제지표 이후 Fed 해석
- ZeroHedge: 비주류 리스크 서사와 시장 불안 심리
- The Economist: 글로벌 정책 흐름과 고급 차트
- IsabelNet: 매일 나오는 데이터 시각화
- FactSet: 주간 단위 실적/시장 분석

Analysis River는 엄격한 순위가 아니라 역할 분담에 가깝다. 좋은 방송 재료는 반드시 최신 속보일 필요가 없다. FactSet처럼 주간 단위 자료도 오늘 시장을 설명하는 핵심 근거가 될 수 있다.

## 7. 주요 파이프라인 단계

### 7.1 Browser/CDP Health Check

호스트 Chrome이 열려 있고 Docker가 CDP로 접근 가능한지 확인한다. Finviz, X, CNN, Yahoo Finance 등 동적 사이트 캡처가 필요하므로 브라우저 상태가 중요하다.

### 7.2 Source Collection

뉴스, X, Yahoo RSS, Finviz, 분석 계정, 차트 후보를 모은다. 이 단계는 최대한 넓게 받는 쪽에 가깝다. 이후 단계에서 ranking과 filtering을 한다.

### 7.3 Chart Capture and Datawrapper

시장 차트와 표를 수집하고 Datawrapper 그래프를 업데이트한다. Notion과 그래프 부제의 기준 시점을 최대한 일치시킨다.

### 7.4 Market Radar

수집된 100~300개 안팎의 자료를 후보 목록으로 정리한다. source weight, recency, theme match, visual availability, source quality adjustment를 합쳐 우선순위를 만든다.

Market Radar는 “많은 자료 중 무엇이 오늘 볼 만한가”를 정리하는 자료 선별 데스크다. 이 단계는 LLM이 마음대로 순위를 정하는 것이 아니라 local scoring과 source policy가 중심이다.

### 7.5 Evidence Microcopy

각 자료가 말하는 핵심을 짧게 요약한다. 기본 모델은 `gpt-5-mini`다.

목표는 최종 문장을 예쁘게 쓰는 것이 아니라, 내부 자료 창고를 방송용으로 읽히게 정리하는 것이다. 자료 하나마다 핵심 내용을 1~3문장으로 정리하고, 최종 Notion에서는 문장 단위 bullet로 보여줄 수 있다.

이 단계도 자료 채택, 순서, ranking을 바꾸지 않는다.

### 7.6 Market Focus Brief

고급 모델이 시장 근거를 검증한다. 어떤 이슈가 실제 가격 반응, 차트, 기사, 한국장 연결점을 갖고 있는지 본다.

주요 판단은 다음과 같다.

- 이 이슈가 오늘 시장에서 실제로 중요했는가
- 가격 반응과 뉴스 근거가 같은 방향인가
- source gap이 있는가
- false lead 가능성이 있는가
- 첫 5분 방송에서 다룰 만한가

### 7.7 Editorial Brief

고급 모델이 방송의 편집 흐름을 잡는다. Market Focus가 증권부 데스크라면 Editorial Brief는 편집국장이다.

주요 판단은 다음과 같다.

- 오늘 톱스토리는 무엇인가
- 3개 스토리라인의 순서는 어떤가
- 진행자가 첫 5분에 어떻게 열어야 하는가
- 한국장과 개인투자자에게 어떤 연결점이 있는가
- PPT 슬라이드는 어떤 흐름으로 이어지는가

### 7.8 Dashboard Microcopy

최종 Notion에 들어갈 짧은 공개 문장을 다듬는다. 기본 모델은 `gpt-5-mini`다.

이 단계는 카피 에디터다. 구조, 순서, 카드명, 섹션을 바꾸지 않고 다음 값만 생성하거나 다듬는다.

- 진행자용 요약 quote
- 스토리라인 quote
- `왜 중요한가`
- 미디어 포커스 `주요 내용`

### 7.9 Renderer

renderer는 최종 publish Markdown의 형태를 고정한다. LLM output은 값으로만 받아오고, 최종 문서 구조는 renderer가 만든다.

현재 Notion 구조는 크게 다음과 같다.

```text
문서 생성 / 자료 수집 / 시장 차트 기준

# 진행자용 요약
  - 오늘의 quote
  - 주요 뉴스
  - 방송 순서
  - 스토리라인 3개

# 자료 수집
  ## 1. 시장은 지금
  ## 2. 미디어 포커스
  ## 3. 실적/특징주
```

### 7.10 Quality Gate

발행 직전 계약 검사를 한다. 실패하면 publish policy에 따라 Notion 발행을 막는다.

대표 검사 항목은 다음과 같다.

- compact format 유지
- 스토리라인 3개
- quote 길이와 개수
- `왜 중요한가` bullet 개수
- slide line과 미디어 포커스 카드명 일치
- `## 1. 시장은 지금`에 `요약:`/`내용:` 없음
- 주요 지수 흐름 2개
- FedWatch 단기/장기
- 미디어 포커스 카드의 주요 내용 존재
- publish Markdown에 role/id/hash/URL leak 없음

### 7.11 Notion Publish

quality gate 통과 후 Notion 페이지를 교체 발행한다. 원칙적으로 Notion publish는 사용자가 직접 보게 될 최종 화면만 다룬다. 내부 id, source role, trace 정보는 publish Markdown에 노출하지 않는다.

### 7.12 Sourcebook

sourcebook은 내부 장부다. 어떤 자료가 들어왔고, 어떤 판단이 있었고, microcopy가 얼마나 fallback 되었는지 기록한다.

sourcebook에는 내부 id와 trace를 남길 수 있다. 다만 credentials, signed URL, raw HTML, full article body, full X text는 넣지 않는다.

## 8. LLM 역할: 신문사 비유

Autopark의 LLM들은 하나의 큰 모델이 모든 것을 결정하는 구조가 아니다. 신문사 편집국처럼 역할이 나뉘어 있다.

| 단계 | 신문사 비유 | 모델 | 하는 일 | 하지 않는 일 |
|---|---|---|---|---|
| Preflight Agenda | 조간 편집회의 전 뉴스 에디터 | `gpt-5.5` | 밤사이 주요 의제와 확인 질문을 제안 | 최종 기사 배치 확정 |
| Evidence Microcopy | 자료 정리 인턴 또는 리서처 | `gpt-5-mini` | 자료 하나하나의 핵심을 짧게 요약 | 자료 채택/순위 결정 |
| Market Focus | 증권부 데스크 | `gpt-5.5` | 시장 근거, 가격 반응, source gap 검증 | publish 형식 변경 |
| Editorial Brief | 편집국장 | `gpt-5.5` | 톱스토리, 방송 흐름, 한국장 연결점 결정 | 카드명/번호 임의 변경 |
| Dashboard Microcopy | 카피 에디터 | `gpt-5-mini` | 최종 공개 문장을 매끄럽게 다듬음 | 구조/순서/자료명 변경 |

이 비유에서 중요한 점은 “편집국장도 조판 시스템을 마음대로 바꾸지 않는다”는 것이다. 최종 지면, 즉 Notion compact dashboard의 구조는 renderer가 소유한다.

## 9. Publish 문서의 철학

Autopark의 최종 Notion 문서는 분석 리포트라기보다 진행자 큐시트다. 따라서 상단은 길어지면 안 된다.

원칙은 다음과 같다.

- 상단은 진행자가 읽는 큐시트
- 시장 섹션은 실제 PPT 시장지도 순서
- 미디어 포커스는 통합 자료 창고
- 실적/특징주는 별도 섹션
- publish Markdown에는 role/id/hash 노출 금지
- 깊이는 내부 엔진과 미디어 카드 주요 내용에서 확보
- 자료가 없거나 캡처가 실패하면 부정확한 과거 자료를 넣지 않고 공란 처리

## 10. 시각화용 요약

이미지로 그린다면 아래 구조가 가장 이해하기 쉽다.

```text
[05:00 Docker Scheduler]
        |
        v
[Host Chrome CDP / Browser Auth]
        |
        v
[Source Collection]
   |             |              |
   v             v              v
[Market Data] [Headline River] [Analysis River]
   |             |              |
   v             v              v
[Charts/Datawrapper]      [Raw + Processed Evidence]
        \                  /
         \                /
          v              v
             [Market Radar]
                    |
                    v
          [Evidence Microcopy]
                    |
                    v
             [Market Focus]
                    |
                    v
            [Editorial Brief]
                    |
                    v
          [Dashboard Microcopy]
                    |
                    v
              [Renderer]
                    |
                    v
             [Quality Gate]
              |          |
              v          v
          [Notion]   [Blocked + Report]
                    |
                    v
              [Sourcebook]
```

신문사 비유로 그린다면 다음처럼 표현할 수 있다.

```text
뉴스 에디터
  -> 자료 리서처
  -> 증권부 데스크
  -> 편집국장
  -> 카피 에디터
  -> 조판 시스템
  -> 발행 심사
  -> Notion 신문 1면
```

## 11. 이미지 생성 프롬프트 초안

아래 문단은 이미지 모델에 바로 줄 수 있는 설명이다.

```text
Create a clean Korean workflow infographic for an automated market-news newsroom called Autopark.

Show the flow from top to bottom:
05:00 Docker Scheduler -> Host Chrome CDP -> Source Collection -> three source rivers:
1. Market Data, 2. Headline River, 3. Analysis River.
Then merge into Market Radar -> Evidence Microcopy -> Market Focus -> Editorial Brief -> Dashboard Microcopy -> Renderer -> Quality Gate -> Notion Publish + Sourcebook.

Use a newsroom metaphor:
Preflight Agenda as morning news editor,
Evidence Microcopy as research assistant,
Market Focus as securities desk,
Editorial Brief as editor-in-chief,
Dashboard Microcopy as copy editor,
Renderer as layout desk,
Quality Gate as final proof desk.

Style: readable operations diagram, not marketing.
Use compact boxes, arrows, restrained colors, Korean labels, and a side legend explaining data sources:
Market Data, Yahoo ticker RSS, official X news accounts, BizToc/Finviz fallback, Kobeissi Letter, Wall St Engine, Liz Ann Sonders, Charlie Bilello, Nick Timiraos, ZeroHedge, The Economist, IsabelNet, FactSet.

Emphasize that LLMs do not control final layout, source order, card names, or ranking. They only provide judgment and short public-facing microcopy. Renderer owns the final Notion compact dashboard structure.
```

## 12. 현재 기준 다음 관찰 포인트

내일 실제 자동화 이후에는 다음을 보면 된다.

- 05:00 실행이 정상 시작했는가
- host Chrome CDP가 살아 있었는가
- Finviz/X/CNN 캡처가 정상인지
- market radar 후보 수와 상위 후보 품질이 적절한지
- Yahoo ticker RSS와 공식 X 뉴스 계정이 충분히 들어왔는지
- Analysis River에서 저빈도 계정이 72h lookback으로 잘 잡혔는지
- Evidence Microcopy가 자료 핵심을 과하게 딱딱하게 만들지 않았는지
- Market Focus와 Editorial Brief가 서로 역할을 침범하지 않는지
- Quality Gate가 실제로 publish를 막아야 할 경우 막는지
- Notion 문서가 진행자 큐시트로 읽히는지
