# Notion Report Pipeline

이 문서는 Datawrapper와 Notion을 연결해 보고서 초안을 자동 생성하는 방향을 정리한 메모다.

## Bottom Line

Notion API가 있으면, 이 저장소에서 만든 차트와 문장을 바탕으로 **보고서 초안 페이지를 자동 생성하는 것**은 충분히 가능하다.

즉 아래 흐름이 가능하다.

1. `incoming/` 원본 CSV 수신
2. `prepared/` 차트용 CSV 생성
3. Datawrapper 차트 생성 및 publish
4. chart 이미지 또는 URL 확보
5. Notion 페이지 생성
6. 섹션 제목, 핵심 해석, 이미지, source, note를 블록 단위로 삽입

## What The Notion API Can Do

2026-04-11 기준 공식 문서상 가능한 것:

- 페이지 생성
- 블록 append
- 이미지/파일 블록 추가
- 외부 URL 기반 파일 참조
- API 업로드 파일을 블록에 첨부

공식 문서:

- [Append block children](https://developers.notion.com/reference/patch-block-children)
- [Working with page content](https://developers.notion.com/docs/working-with-page-content)
- [Working with files and media](https://developers.notion.com/guides/data-apis/retrieving-files)
- [File object](https://developers.notion.com/reference/file-object)
- [File Upload](https://developers.notion.com/reference/file-upload)
- [Uploading small files](https://developers.notion.com/guides/data-apis/uploading-small-files)
- [Importing external files](https://developers.notion.com/guides/data-apis/importing-external-files)

## Practical Pipeline Design

### Option A: External image URLs

가장 단순한 방식이다.

1. Datawrapper publish 또는 이미지 URL 확보
2. Notion 페이지 생성
3. 이미지 블록을 `external` URL로 삽입
4. 아래에 caption, source, note를 문단 블록으로 추가

장점:

- 구현이 단순하다
- 로컬 파일 업로드 절차가 없다

주의:

- URL이 안정적으로 접근 가능해야 한다
- private asset 운영에는 불리할 수 있다

### Option B: Notion file upload

더 견고한 방식이다.

1. Datawrapper에서 PNG export 확보
2. Notion File Upload API로 업로드
3. 업로드된 파일을 이미지 블록에 attach
4. 본문 블록과 함께 보고서에 배치

장점:

- 자산을 Notion 쪽에 붙잡아둘 수 있다
- 외부 URL 만료 리스크가 줄어든다

주의:

- 업로드 단계가 추가된다
- 실제 export 방식과 파일 크기 제한을 함께 테스트해야 한다

## Recommended Report Shape

초안 자동 생성은 아래처럼 가면 가장 실용적이다.

1. 보고서 제목
2. 한 줄 요약
3. 핵심 차트 1
4. 해석 문단
5. 핵심 차트 2
6. 해석 문단
7. 핵심 차트 3
8. 해석 문단
9. source / note / update time

즉 완성본을 자동 작성하기보다, **사람이 바로 고칠 수 있는 탄탄한 초안**을 목표로 하는 것이 맞다.

## Good First Use Case

첫 자동화 대상으로는 `wepoll-samsung`이 좋다.

이유:

- 메시지가 비교적 명확하다
- prepared CSV 4종이 이미 있다
- 차트 순서가 자연스럽다
- 발표용 narrative가 이미 정리돼 있다

추천 첫 배치:

- consensus
- level participation
- level accuracy
- staff dot plot

## Suggested Implementation Stages

### Stage 1

- Notion API로 빈 보고서 페이지 생성
- 제목, 소제목, 문단 블록만 자동 생성

### Stage 2

- Datawrapper 차트 URL 또는 이미지 삽입
- source / note 문구 자동 첨부

### Stage 3

- project별 템플릿화
- `prepared/` CSV와 차트 spec을 읽어 보고서 초안 완성

## Operating Principle

이 파이프라인의 목적은 사람을 대체하는 것이 아니다.

목표는 아래 둘이다.

- 초안 작성 시간을 줄이기
- 차트와 문안의 구조를 반복 가능하게 만들기

최종 검수, 문장 선택, 발표용 발췌는 사람이 하는 것이 가장 안전하다.

## Resume Status

2026-04-11 기준 현재 상태:

- `wepoll-samsung` first batch 차트 메시지가 이미 정리돼 있다
- Notion으로 보낼 만한 차트 후보 4종이 prepared CSV로 준비돼 있다
- 아직 Notion 페이지 생성 스크립트, 블록 템플릿, 데이터 매핑 파일은 없다

따라서 첫 목표는 "완성 보고서 생성"이 아니라 "초안 페이지 1개 자동 생성"이다.

## Dependencies From Datawrapper

Notion 초안 자동화는 아래 둘 중 하나가 먼저 준비돼야 한다.

- Datawrapper publish URL
- Datawrapper PNG export 파일

즉 실무 순서는 대체로 아래가 맞다.

1. Datawrapper chart 생성 및 publish
2. chart URL 또는 이미지 자산 확보
3. Notion 초안 페이지 생성

## Minimal Notion Setup

필요한 값:

- `NOTION_API_KEY`
- `NOTION_PARENT_PAGE_ID` 또는 데이터베이스를 쓸 경우 `NOTION_DATABASE_ID`

운영 원칙:

- API 키는 코드에 넣지 않는다
- 먼저 빈 테스트 페이지 1개를 만드는 것으로 인증을 검증한다
- 초안 대상은 페이지 한 개로 제한해서 구조를 먼저 고정한다

## Suggested First Draft Shape

`wepoll-samsung` 기준 추천 초안 구조:

1. 보고서 제목
2. 한 줄 요약
3. consensus 차트
4. 해석 문단
5. level participation 차트
6. 해석 문단
7. level accuracy 차트
8. 해석 문단
9. staff dot plot
10. 해석 문단
11. source / note / 작성 시각

## Recommended Input Contract

Notion 자동화는 처음부터 CSV를 직접 해석하기보다, 차트별 구조화된 입력을 받는 편이 안정적이다.

최소 입력 항목:

- chart title
- subtitle
- key takeaway
- source
- note
- publish URL 또는 local export path

이 입력은 차트 스펙 문서나 별도 JSON 파일로 관리할 수 있다.

## Recommended Script Scope

처음 버전은 아래 정도면 충분하다.

- 페이지 생성
- heading / paragraph 블록 추가
- 차트 이미지 또는 링크 삽입
- source / note / update time 추가

예시 방향:

- `scripts/notion_create_report_draft.py`

첫 버전에서 굳이 하지 않아도 되는 것:

- 복잡한 데이터베이스 속성 매핑
- 여러 프로젝트 동시 지원
- 차트별 세부 레이아웃 분기

## Definition Of Done

이 문서 기준으로 "Notion 초안 작성 API 연결 완료"의 최소 조건은 아래다.

1. 로컬에서 Notion 인증 성공
2. 테스트용 페이지 1개 생성
3. 제목, 요약, 차트 섹션 2개 이상 자동 삽입
4. 차트 URL 또는 이미지가 본문에 포함
5. 사람이 바로 수정 가능한 수준의 초안이 생성

여기까지 되면 이후에는 보고서 템플릿화와 프로젝트 확장이 쉬워진다.
