# Wepoll Windows Server Runbook

기준일: 2026-04-21

이 문서는 Windows PC를 위폴 daily update 서버처럼 운영할 때의 최소 실행 절차를 정리한다.

## Recommended Split

권장 구조:

- Playwright fetcher: Windows 사용자 세션에 상시 실행
- compute/publish batch: 필요하면 Docker, 아니면 로컬 Python 실행

첫 버전에서는 둘 다 로컬에서 돌리는 것이 가장 단순하다.
브라우저 로그인 세션 문제가 정리된 뒤 계산 파트만 Docker로 분리해도 늦지 않다.

이번 기준부터는 `wepoll-panic` 계산부도 `zsh` 없이 Python runner로 호출된다.
즉 Windows에서 `buykings + wepoll-panic` sibling checkout만 맞추면 바로 1차 이관 테스트가 가능하다.

## One-Time Setup

Windows용 starter 세트는 [ops/windows/README.md](/Users/bae/Documents/code/buykings/ops/windows/README.md)에 모아뒀다.
Windows PC의 Codex handoff는 [ops/windows/codex-handoff.md](/Users/bae/Documents/code/buykings/ops/windows/codex-handoff.md)를 먼저 보면 된다.

### 1. Clone repo

```powershell
cd C:\ops
git clone <buykings-repo>
git clone <wepoll-panic-repo>
cd buykings
```

권장 배치:

- `C:\ops\buykings`
- `C:\ops\wepoll-panic`

### 2. Python env

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
```

현재 `wepoll-panic` daily subset은 표준 라이브러리만으로 실행되도록 맞춰져 있다.
즉 1차 마이그레이션 기준 추가 Python 패키지 설치는 필수가 아니다.

### 3. Node + Playwright

```powershell
npm install
```

### 4. Environment file

`.env`에 최소 아래 값이 필요하다.

- `DATAWRAPPER_ACCESS_TOKEN`
- Notion 연동 시 `NOTION_API_KEY`
- LLM 실행에 필요한 키나 로컬 모델 환경 변수
- 필요 시 `WEPOLL_PANIC_ROOT`

## Start Fetcher

### 1. Headed login boot

```powershell
npm run wepoll:fetcher -- `
  --user-data-dir runtime\wepoll-fetcher-profile `
  --browser-path "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --headed `
  --allow-manual-login `
  --verbose
```

브라우저 창이 뜨면 사람이 네이버 로그인 1회만 한다.

로그인 후 브라우저는 닫지 않는다.

### 2. Health check

```powershell
curl http://127.0.0.1:8777/health
```

정상일 때:

- `authenticated: true`
- `page_url`가 `mypage_data.php`

## Daily Run

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py
```

이 명령은:

1. fetcher health 확인
2. `최근 3일` 위폴 CSV 다운로드
3. `scripts/run_wepoll_daily_append.py` 실행
4. `scripts/wepoll_sync_sqlite.py` 실행

까지 한 번에 처리한다.

다른 위치의 `wepoll-panic`를 쓰고 싶다면:

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py `
  --panic-root D:\repos\wepoll-panic
```

상위 morning 오케스트레이터로 돌리고 싶다면:

```powershell
.\.venv\Scripts\python.exe scripts\run_buykings_morning.py
```

현재는 이 runner 아래에 `wepoll-panic` job만 연결돼 있다.

## Useful Flags

### Download만 테스트

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py --skip-append --skip-sqlite-sync
```

### Publish 없이 append

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py --skip-publish
```

### OpenAI backend로 2차 판정

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py `
  --second-pass-backend openai `
  --model gpt-5-mini
```

### 특정 날짜 강제

```powershell
.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py --target-date 2026-04-21
```

## Task Scheduler Recommendation

권장:

- fetcher는 Windows 로그인 사용자 세션에서 항상 실행
- daily batch만 Task Scheduler로 호출

예:

- 매일 오전 11:35: `python scripts\run_wepoll_daily_from_fetcher.py`

## Failure Recovery

### `/health`에서 인증 실패

대응:

- fetcher 브라우저 창으로 돌아가 재로그인
- 다시 `/health` 확인

### fetcher 프로세스 종료

대응:

- fetcher 재기동
- 필요 시 1회 재로그인

### download는 성공했는데 append 실패

대응:

- `runtime\downloads\wepoll\*.csv` 보관본 재사용
- `scripts\run_wepoll_daily_append.py --input <csv>`로 재시도

## Next Step

여기까지 안정화되면 다음으로 붙일 것:

1. 로고 포함 PNG export 경로 정리
2. Notion 이미지 블록 교체 자동화
3. compute 파트를 Docker로 분리
