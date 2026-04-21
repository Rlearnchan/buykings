# Wepoll Automation Plan

기준일: 2026-04-21

이 문서는 `buykings`의 현재 수동 운영을

- 다른 Windows PC에서
- Docker 기반으로 옮기고
- daily update부터 Datawrapper/Notion 갱신까지
- 가능한 범위에서 무인 자동화

하는 계획을 정리한다.

## Goal

최종 목표는 아래 한 줄이다.

`위폴 raw 데이터 수급 -> 지수 산출 -> Datawrapper append/publish -> 로고 포함 PNG export -> 같은 Notion 페이지 이미지 교체`

를 매일 자동 실행하고, 실패하면 사람이 바로 개입할 수 있게 만드는 것.

## Current Status

현재 저장소 기준으로 이미 자동화돼 있는 부분:

- 시장 데이터 fetch
- daily additive 실행
- append-only 지수 계산
- prepared CSV 갱신
- Datawrapper publish
- 로고 오버레이 PNG export

현재 수동으로 남아 있는 부분:

- 위폴 raw CSV 수급
- Notion 페이지 이미지 갱신
- 최종 결과 QA

## Tested Hurdle

`2026-04-21`에 실제 위폴 다운로드 페이지에서 아래 플로우를 확인했다.

- URL: `https://wepoll.kr/g2/bbs/mypage_data.php`
- 로그인 세션이 살아 있으면 직접 진입 가능
- 기간 `최근 3일` 선택 가능
- 게시판 `경제`, 포함 범위 `글만`, 형식 `CSV` 기본값 확인
- 다운로드 버튼 클릭 시 파일 저장 확인
- 실제 저장 파일: `~/Downloads/wepoll_stock_posts_2026-04-18_2026-04-21.csv`

즉 마지막 허들은 "기술적으로 가능한가"가 아니라
"서버에서 로그인 세션을 얼마나 안정적으로 유지할 것인가" 쪽에 가깝다.

## Recommendation

### Browser automation

권장: `Playwright`

이유:

- 다운로드 대기와 저장이 Selenium보다 단순하다.
- headless/headed 전환이 쉽다.
- persistent profile 또는 storage state를 쓰기 좋다.
- Docker 이미지가 비교적 잘 정리돼 있다.
- 지금처럼 사이트 구조를 먼저 탐색하고 나중에 코드로 옮기기 좋다.

비권장: `Codex Computer Use`를 운영 본체로 쓰는 방식

이유:

- 탐색과 프로토타이핑에는 유용하지만 서버에서 매일 무인 실행하는 주체로는 맞지 않는다.
- 상태 복원, 재시도, 스케줄링, 로그 관리가 브라우저 테스트 러너보다 약하다.

Selenium은 가능하지만, 이 저장소는 Python 위주이더라도 다운로드/대기/세션 보존 면에서 Playwright가 더 낫다.

단, 이 프로젝트의 위폴 다운로드는 "새 브라우저 재실행 후 로그인 상태 복원"보다
"로그인된 Playwright 브라우저를 장기 실행하고 그 세션을 재사용"하는 쪽이 더 유력하다.

## Target Architecture

권장 구성은 3계층이다.

### 1. Scheduler

Windows 서버에서 아래 둘 중 하나를 쓴다.

- Windows Task Scheduler
- Docker Compose + 단발 실행 스크립트

권장 방식:

- 매일 오전 고정 시각에 Task Scheduler가 `docker compose run --rm daily-update`를 호출
- 실패 시 로그 파일과 종료 코드를 남김

### 2. Pipeline container

이 컨테이너는 계산과 발행을 담당한다.

포함 역할:

- 위폴 다운로드 실행
- raw CSV를 지정 폴더로 이동
- `scripts/run_wepoll_daily_append.py` 실행
- Datawrapper PNG export + 로고 삽입
- Notion 이미지 갱신
- SQLite sync 또는 실행 로그 저장

### 3. Persistent volumes

아래는 컨테이너 외부 볼륨으로 유지한다.

- repo working copy
- `.env`
- browser auth profile 또는 Playwright storage state
- raw downloads archive
- generated PNG archive
- logs

## Proposed Daily Flow

### Step 1. Wepoll download

- Playwright가 `mypage_data.php`로 접속
- `최근 3일` 선택
- `경제`, `글만`, `CSV` 확인
- 다운로드 파일 저장
- 파일명과 다운로드 시각 기록

### Step 2. Raw normalization

- 다운로드 파일을 `incoming/raw/` 같은 보관 폴더로 이동
- 같은 파일이 이미 처리된 적 있으면 hash 비교 후 skip
- 파일명에서 날짜 범위 추출

### Step 3. Daily append

- `scripts/run_wepoll_daily_append.py --input <downloaded_csv>`
- 완전히 닫힌 최근 날짜만 append
- Datawrapper publish까지 수행

### Step 4. PNG export

- timeseries / bubble PNG export
- 로고 오버레이 적용
- `exports/wepoll-panic/weekly/current/`와 발표일 스냅샷 경로 모두 갱신

### Step 5. Notion refresh

- 같은 Notion 페이지의 기존 이미지 블록 위치를 유지
- 새 PNG로 교체
- 교체 전후 블록 id / 실행 결과 기록

### Step 6. Logging and alerting

- 성공 시 실행 로그 JSON 저장
- 실패 시 stderr + 단계명 + 마지막 URL 또는 파일 경로 기록
- 가능하면 Slack 또는 이메일 알림 추가

## Container Split

실제로는 하나로도 가능하지만, 운영은 아래처럼 나누는 편이 안정적이다.

### Option A. one container

장점:

- 가장 단순하다.

단점:

- 브라우저 인증 문제와 계산 파이프라인이 강하게 결합된다.

### Option B. two containers

- `wepoll-fetcher`
- `daily-pipeline`

권장안은 이것이다.

이유:

- 다운로드 실패와 계산 실패를 분리할 수 있다.
- 인증 프로필 볼륨을 fetcher에만 묶을 수 있다.
- 나중에 Notion updater를 별도 작업으로 떼기 쉽다.

## Auth Strategy

가장 중요한 운영 포인트다.

### Preferred

장기 실행 fetcher 프로세스가 전용 Playwright 브라우저를 띄운 뒤,
초기 1회만 사람이 직접 로그인한다.

그 뒤에는 브라우저를 끄지 않고 유지하면서
로컬 HTTP endpoint를 통해 다운로드만 요청한다.

즉 "세션을 복구"하는 대신 "세션을 안 죽이는" 전략이다.

구체 운영은 [wepoll-long-lived-fetcher.md](./wepoll-long-lived-fetcher.md)를 따른다.

### Fallback

전용 user data dir 재사용 또는 storage state 파일 재사용.

하지만 현재 위폴 + 네이버 소셜 로그인 조합에서는 이 방법이 장기 실행 브라우저보다 덜 안정적으로 보인다.

## Notion Strategy

현재 저장소에는 Notion 갱신 코드가 없다.

따라서 첫 자동화 버전은 아래 두 단계로 가는 것이 좋다.

### Phase 1

- 계산 + Datawrapper + PNG export + 파일 보관까지 자동화
- Notion은 사람이 마지막으로 확인 후 수동 반영

### Phase 2

- 같은 Notion 페이지의 이미지 블록 교체 자동화

구현 후보:

- Notion API를 써서 특정 블록을 새 이미지로 교체
- API 제약이 크면 Playwright로 Notion 웹 UI 자동화

권장 우선순위:

- API 먼저 검토
- 막히면 브라우저 자동화로 폴백

## Docker Notes

Windows 서버에 올릴 때는 Linux container 기준을 권장한다.

이유:

- Playwright 공식 이미지 활용이 쉽다.
- Python 파이프라인 의존성 정리가 단순하다.

권장 볼륨:

- `./runtime/env`
- `./runtime/wepoll-profile`
- `./runtime/downloads`
- `./runtime/logs`
- `./exports`
- `./projects/wepoll-panic/state`

권장 secrets:

- `DATAWRAPPER_ACCESS_TOKEN`
- Notion integration secret
- 필요 시 OpenAI/LLM 관련 키

## Failure Modes

### Wepoll auth expired

증상:

- 다운로드 페이지가 로그인 페이지로 리다이렉트
- 또는 다운로드 버튼 클릭 후 실패

대응:

- headed 모드로 1회 재로그인
- profile volume 유지 여부 확인

### Downloaded file is incomplete

증상:

- 오늘 날짜만 포함되고 닫히지 않은 날짜가 선택됨

대응:

- 기존처럼 `run_wepoll_daily_append.py`의 auto-select 로직이 최종 방어선 역할
- 원시 파일은 넓게 받아도 append는 닫힌 날짜만 반영

### Notion block replacement fails

대응:

- PNG 생성까지는 성공 처리
- Notion만 별도 실패 단계로 기록
- 사람이 이미지 2장만 수동 교체 가능하게 산출 경로를 고정

## Rollout Plan

### Phase 0. local prototype

- 위폴 다운로드 Playwright 스크립트 작성
- headed 모드에서 서버 후보 환경과 같은 방식으로 검증

### Phase 1. fetch automation

- 위폴 다운로드를 스케줄러로 자동 실행
- raw CSV 보관과 dedupe 확인

### Phase 2. compute + publish

- download -> append -> Datawrapper publish까지 한 번에 연결

### Phase 3. image automation

- 로고 포함 PNG export
- 발표일/최신본 경로 정리

### Phase 4. Notion automation

- 동일 페이지 이미지 블록 교체
- 실패 알림 추가

## Immediate Next Steps

1. Playwright 기반 `wepoll` 다운로드 스크립트를 이 저장소에 넣는다.
2. 서버에서는 persistent browser profile을 쓰는 방식으로 1차 운영한다.
3. 다운로드 파일 보관 경로와 daily append 입력 경로를 연결하는 wrapper 스크립트를 만든다.
4. Notion 업데이트는 API 가능 여부를 별도 확인한 뒤 2차로 붙인다.
