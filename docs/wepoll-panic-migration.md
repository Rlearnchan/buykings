# Wepoll-Panic Migration

기준일: 2026-04-21

이 문서는 `buykings-morning` 아래 첫 이관 대상으로
`wepoll-panic`을 Windows 서버로 옮길 때의 실제 기준을 정리한다.

핵심 결론은 단순하다.

- `위폴 로그인/다운로드`는 Windows 호스트에 남긴다.
- `wepoll-panic 계산부`는 우선 로컬 Python으로 옮긴다.
- Docker 분리는 계산부가 며칠 안정화된 뒤 2차로 한다.

## Why This First

`wepoll-panic`은 현재 morning 트랙 중에서

- 입력이 명확하고
- 산출물이 명확하고
- fetcher와 계산부 경계가 이미 생겼고
- Notion 같은 후속 작업을 떼어낼 수 있어서

가장 먼저 옮기기 좋은 job이다.

## Phase 1 Target

이번 1차 마이그레이션의 목표는 아래다.

1. Windows 로그인 세션에서 `wepoll-fetcher` 상시 실행
2. 같은 서버에서 `buykings`와 `wepoll-panic`를 함께 checkout
3. `run_wepoll_daily_from_fetcher.py`로 daily batch 실행
4. `buykings-morning`이 상위 엔트리포인트 역할 수행

즉 첫 단계에서는
`host fetcher + local Python compute`
조합으로 끝낸다.

## Required Repo Layout

현재 기준 권장 배치는 sibling 구조다.

```text
C:\ops\
  buykings\
  wepoll-panic\
```

이때 `buykings`는 기본적으로 아래를 찾는다.

- `..\wepoll-panic`

다른 위치를 쓰고 싶으면 환경 변수 또는 CLI로 덮어쓴다.

- `WEPOLL_PANIC_ROOT`
- `--panic-root`

## Portable Change

이번 기준부터 `buykings`는 더 이상 `zsh run_daily_server_batch.sh`에만 묶이지 않는다.

새 엔트리포인트:

- [run_wepoll_panic_daily_batch.py](/Users/bae/Documents/code/buykings/scripts/run_wepoll_panic_daily_batch.py)

역할:

- `wepoll-panic`의 daily compute 단계를 Python만으로 실행
- Windows에서도 동일하게 동작
- `ollama` 또는 `openai` 2차 판정 backend 선택 가능

즉 `run_wepoll_daily_append.py`는 이제 내부적으로
이 portable runner를 호출한다.

## One-Time Server Setup

### 1. Clone both repos

```powershell
git clone <buykings-repo>
git clone <wepoll-panic-repo>
```

### 2. Python env

```powershell
cd buykings
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
```

현재 `wepoll-panic` daily subset은 별도 third-party Python 패키지 없이도 돌아가도록 맞췄다.
즉 1차 마이그레이션 기준 필수 Python 의존성은 표준 라이브러리다.

### 3. Node + Playwright

```powershell
npm install
```

### 4. Environment

최소한 아래 값은 준비한다.

- `DATAWRAPPER_ACCESS_TOKEN`
- `OPENAI_API_KEY` 또는 Ollama 환경
- 필요 시 `WEPOLL_PANIC_ROOT`

## First Live Test

### 1. Fetcher boot

```powershell
npm run wepoll:fetcher -- `
  --user-data-dir runtime\wepoll-fetcher-profile `
  --browser-path "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --headed `
  --allow-manual-login
```

### 2. Download-only test

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py `
  --skip-append `
  --skip-sqlite-sync
```

### 3. Full `wepoll-panic` test

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py `
  --panic-root ..\wepoll-panic `
  --skip-sqlite-sync
```

상위 runner로 확인하려면:

```powershell
.\.venv\Scripts\python.exe scripts\run_buykings_morning.py --job wepoll-panic
```

## Backend Choice

기본값은 기존 운영과 맞춘 `ollama`다.

하지만 Windows 서버 안정성을 우선하면 `openai`가 더 나을 수 있다.

예:

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py `
  --panic-root ..\wepoll-panic `
  --second-pass-backend openai `
  --model gpt-5-mini
```

여기서 `model`은 `wepoll-panic` 2차 판정에 쓰는 모델이다.

## What We Are Not Moving Yet

이번 단계에서는 아래를 일부러 뒤로 둔다.

- Notion 이미지 교체
- `capture-and-collect`
- Docker containerized compute
- API delivery 고도화

즉 1차 목표는
`wepoll-panic daily job이 Windows 서버에서 스스로 돈다`
까지다.

## Phase 2

1차가 안정화되면 그다음은 아래 순서가 자연스럽다.

1. Task Scheduler에 `buykings-morning` 등록
2. `wepoll-panic` daily job 며칠 운영 검증
3. 계산부만 Docker로 분리
4. `capture-and-collect` job 추가
5. 마지막에 Notion job 추가

## Windows Codex Handoff

Windows 서버 PC에도 Codex가 있다면,
아래 starter 세트를 바로 넘기면 된다.

- [ops/windows/README.md](/Users/bae/Documents/code/buykings/ops/windows/README.md)
- [ops/windows/codex-handoff.md](/Users/bae/Documents/code/buykings/ops/windows/codex-handoff.md)
- [ops/windows/server.env.example](/Users/bae/Documents/code/buykings/ops/windows/server.env.example)
- [ops/windows/start_wepoll_fetcher.ps1](/Users/bae/Documents/code/buykings/ops/windows/start_wepoll_fetcher.ps1)
- [ops/windows/run_buykings_morning.ps1](/Users/bae/Documents/code/buykings/ops/windows/run_buykings_morning.ps1)
- [ops/windows/smoke_test_wepoll.ps1](/Users/bae/Documents/code/buykings/ops/windows/smoke_test_wepoll.ps1)

이 세트는 “Windows의 Codex가 이 repo를 열고 바로 이어받는다”는 상황을 전제로 만든다.
