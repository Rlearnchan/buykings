# API Next Steps

이 문서는 장기적으로 Datawrapper API를 이 저장소 workflow에 붙일 때의 최소 방향을 적어둔 메모다.

## Why This Matters

Datawrapper API가 안정적으로 붙으면, 이 저장소는 단순 파일 정리 폴더가 아니라 아래 역할까지 할 수 있다.

- prepared CSV를 기준으로 차트를 반복 생성
- 같은 포맷의 주간 차트를 반자동으로 복제
- chart ID, publish URL, export asset을 일관되게 관리
- 향후 `wepoll-panic` 주간 리포트나 `wepoll-samsung` 이벤트 피겨를 빠르게 재생산

즉 장기적으로는 "내가 직접 Datawrapper 그래프를 그리는 능력"이 이 저장소에 붙는 셈이다.

## Suggested Phases

### Phase 1

- 수동 업로드 + 수동 스타일링
- 이 저장소에 incoming / prepared / chart spec / export 흐름을 정착

### Phase 2

- Datawrapper API 토큰 발급
- 테스트용 chart 1개 생성
- 로컬에서 chart create / data upload / publish 흐름 검증

### Phase 3

- 반복 차트를 템플릿화
- `prepared/*.csv`와 `chart-spec-template.md`를 기준으로 반자동 발행
- project별 chart registry 문서화

## Minimum API Workflow To Test Later

1. chart 생성
2. CSV 업로드
3. metadata 설정
4. publish
5. chart ID와 publish URL 저장

## Good First Automation Targets

- `wepoll-samsung`의 consensus 차트
- `wepoll-samsung`의 level participation 차트
- `wepoll-panic`의 weekly bubble chart

이 셋은 구조가 비교적 명확해서 API 파이프라인 점검용으로 좋다.

## Resume Status

2026-04-11 기준 현재 상태:

- 수동 업로드용 prepared CSV 4종이 `projects/wepoll-samsung/prepared/`에 준비돼 있다
- first batch 차트 메시지가 `projects/wepoll-samsung/charts/first-batch.md`에 정리돼 있다
- 아직 이 저장소 안에는 API 실행 스크립트나 자격증명 로딩 구조는 없다

즉 다음 단계는 "문서 검토"가 아니라 "토큰 연결 후 최소 1개 차트 생성 실험"이다.

## Minimal Build Plan

### Step 1. Credentials

필요한 값:

- `DATAWRAPPER_ACCESS_TOKEN`

운영 원칙:

- 토큰은 코드에 넣지 않는다
- 로컬 셸 환경변수 또는 별도 `.env` 파일에서만 읽는다
- 차트 생성 전 테스트 호출로 인증 성공 여부를 먼저 확인한다

### Step 2. Local Registry Shape

API를 붙이기 시작하면 chart ID와 산출 URL을 남길 자리가 필요하다.

권장 저장 위치:

- `projects/<project>/charts/` 아래 차트 스펙 문서
- 필요하면 추후 `chart-registry.json` 또는 `chart-registry.csv` 추가

최소 기록 항목:

- local slug
- prepared CSV 경로
- chart type
- chart ID
- publish URL
- last publish date

### Step 3. First End-to-End Test

첫 실험은 아래 한 장으로 충분하다.

1. `dw_consensus_vs_actual.csv` 선택
2. 새 chart 생성
3. CSV 업로드
4. 제목과 부제 입력
5. publish
6. chart ID와 URL을 문서에 기록

성공 기준:

- 로컬 prepared CSV 하나가 실제 발행 URL까지 연결된다
- 같은 과정을 두 번째 차트에 반복할 수 있다

### Step 4. Second Test With Reuse

두 번째 실험은 `dw_level_participation.csv`로 한다.

확인 포인트:

- 차트 타입만 바뀌고 흐름은 유지되는가
- metadata payload 구조를 재사용할 수 있는가
- chart 제목, 부제, source, note를 템플릿화할 수 있는가

## Recommended Script Scope

처음부터 큰 자동화로 가지 말고 아래 정도면 충분하다.

- 입력: prepared CSV 경로, chart title, chart type, project slug
- 처리: create -> upload -> metadata update -> publish
- 출력: chart ID, edit URL, publish URL

처음 버전은 CLI 스크립트 하나여도 된다.

예시 방향:

- `scripts/datawrapper_publish.py`

첫 버전에서 굳이 하지 않아도 되는 것:

- 대량 배치 발행
- 복잡한 스타일 preset 동기화
- 프로젝트 전체 자동 스캔

## Definition Of Done

이 문서 기준으로 "Datawrapper API 연결 완료"의 최소 조건은 아래다.

1. 로컬에서 토큰으로 인증 성공
2. prepared CSV 1개를 새 chart로 생성
3. metadata와 title을 설정
4. publish URL 확보
5. 결과를 프로젝트 문서에 기록

여기까지 되면 Notion 초안 자동화로 넘어갈 수 있다.
