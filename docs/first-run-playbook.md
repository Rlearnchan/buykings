# First Run Playbook

이 문서는 이 저장소의 첫 번째 자동화 버전을 실제로 돌릴 때 필요한 준비와 실행 순서를 짧게 정리한 런북이다.

## Goal

이 저장소의 목적은 아래 파이프라인을 반복 가능한 형태로 만드는 것이다.

1. 다른 분석 저장소에서 최종 CSV를 받는다
2. Datawrapper로 정형화된 피겨를 만든다
3. 발행된 차트나 export 자산을 바탕으로 Notion 초안을 만든다

첫 버전은 이 중 아래 둘을 검증한다.

- prepared CSV 1개로 Datawrapper chart를 실제 publish할 수 있는가
- 그 결과를 바탕으로 Notion 초안 페이지를 자동 생성할 수 있는가

## Files Added For V1

- `scripts/datawrapper_publish.py`
- `scripts/notion_create_report_draft.py`
- `.env.example`
- `projects/wepoll-samsung/charts/consensus-datawrapper.json`
- `projects/wepoll-samsung/charts/first-batch-report-draft.json`

## 1. Datawrapper 시작하기

공식 시작점:

- 개발 문서 홈: [developer.datawrapper.de](https://developer.datawrapper.de/)
- 차트 타입 목록: [Visualization Types](https://developer.datawrapper.de/docs/chart-types)
- 생성 튜토리얼: [Creating a Chart](https://developer.datawrapper.de/docs/creating-a-chart)
- 발행 튜토리얼: [Publishing a Visualization](https://developer.datawrapper.de/docs/publishing-a-visualization)

준비:

1. Datawrapper 계정에 로그인한다.
2. API 토큰을 발급받는다.
3. 로컬 셸에서 `DATAWRAPPER_ACCESS_TOKEN` 환경변수로 넣는다.

예시:

```bash
export DATAWRAPPER_ACCESS_TOKEN='dw_...'
```

드라이런:

```bash
python3 scripts/datawrapper_publish.py \
  projects/wepoll-samsung/charts/consensus-datawrapper.json \
  --dry-run
```

실행:

```bash
python3 scripts/datawrapper_publish.py \
  projects/wepoll-samsung/charts/consensus-datawrapper.json
```

성공하면 `chart_id`, `edit_url`, `public_url`가 JSON으로 출력된다.

그다음 해야 할 일:

1. 출력된 `public_url`을 복사한다.
2. `projects/wepoll-samsung/charts/first-batch-report-draft.json`의 `REPLACE_ME`를 실제 차트 URL로 바꾼다.
3. 필요하면 `projects/wepoll-samsung/charts/first-batch.md`에도 chart ID를 기록한다.

## 2. Notion 시작하기

공식 시작점:

- 시작 가이드: [Build your first integration](https://developers.notion.com/guides/get-started/create-a-notion-integration)
- 페이지 생성: [Create a page](https://developers.notion.com/reference/post-page)
- 블록 작업: [Working with page content](https://developers.notion.com/docs/working-with-page-content)
- 블록 append: [Append block children](https://developers.notion.com/reference/patch-block-children)

준비:

1. Notion integrations dashboard에서 internal integration을 만든다.
2. `Configuration` 탭에서 API secret을 복사한다.
3. 초안을 넣을 부모 페이지를 하나 만든다.
4. 그 페이지의 `...` 메뉴에서 `Add Connections`로 방금 만든 integration을 연결한다.
5. 페이지 URL 끝의 32자리 page ID를 복사한다.
6. 로컬 셸에 아래 환경변수를 넣는다.

```bash
export NOTION_API_KEY='secret_...'
export NOTION_PARENT_PAGE_ID='...'
```

실행:

```bash
python3 scripts/notion_create_report_draft.py \
  projects/wepoll-samsung/charts/first-batch-report-draft.json
```

성공하면 생성된 Notion 페이지의 `url`이 JSON으로 출력된다.

## 3. Recommended First Run Order

1. `.env.example`를 참고해 환경변수를 준비한다.
2. `Datawrapper` 드라이런으로 토큰 검증을 한다.
3. `consensus-datawrapper.json`으로 차트 1개를 실제 publish한다.
4. 출력된 공개 URL을 report draft JSON에 반영한다.
5. `Notion` draft script로 페이지 1개를 생성한다.
6. 사람이 초안을 열어 차트 배치와 문안 톤을 다듬는다.

## 4. Notes For This V1

- Datawrapper 스크립트는 현재 차트 생성, CSV 업로드, 기본 metadata 반영, publish까지 담당한다.
- Notion 스크립트는 현재 페이지 생성과 단순 블록 조립에 집중한다.
- 둘 다 Python 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요 없다.
- 첫 버전에서는 배치 발행, PNG 업로드, Notion 데이터베이스 속성 매핑은 일부러 제외했다.
