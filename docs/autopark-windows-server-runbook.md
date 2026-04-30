# Autopark Windows Server Runbook

기준일: 2026-04-30

Autopark는 Windows PC의 로컬 Chrome 세션과 Task Scheduler로 매일 `06:03 KST`에 실행한다. Docker 분리는 Chrome 로그인/캡처가 안정화된 뒤 검토한다.

## Storage Split

- GitHub: 코드, 설정, 운영 문서
- `.env`: 서버 비밀값, Git 제외
- `AUTOPARK_STATE_ROOT`: 날짜별 실행 산출물 mirror
- `projects/autopark/runtime/profiles`와 `.server-state/autopark/profiles`: 브라우저 세션, Git 제외

## One-Time Setup

```powershell
cd C:\ops\buykings
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements-server.txt
npm install
Copy-Item .\ops\windows\server.env.example .\.env
```

`.env`에는 최소 `NOTION_API_KEY`, `DATAWRAPPER_ACCESS_TOKEN`, `OPENAI_API_KEY`, `AUTOPARK_CDP_ENDPOINT`, `AUTOPARK_PUBLISH_POLICY=gate`를 넣는다.

## Chrome Profile

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start_autopark_chrome.ps1
```

처음 뜬 Chrome에서 X, Finviz, Earnings Whispers, CME FedWatch, Polymarket 로그인/보안확인을 끝낸다. 이후 같은 Windows 사용자 세션에서 프로필을 유지한다.

## Smoke Test

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\smoke_test_autopark.ps1
```

확인 항목:

- Chrome CDP health
- Wall St Engine X dry-run
- Finviz heatmap capture
- Datawrapper market dry-run
- Notion publish dry-run

## Daily Run

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\run_autopark_daily.ps1
```

발행 정책은 gate다. `review_dashboard_quality.py`가 pass이면 Notion `YY.MM.DD` 페이지를 replace publish하고, fail이면 발행하지 않는다.

## Task Scheduler

권장:

- `05:55 KST`: `start_autopark_chrome.ps1`
- `06:03 KST`: `run_autopark_daily.ps1`

두 작업 모두 “사용자가 로그인한 경우에만 실행”으로 둔다. Chrome 로그인 세션이 필요하기 때문이다.

## Outputs

로컬 기본 산출물:

- `projects/autopark/runtime/notion/YYYY-MM-DD/YY.MM.DD.md`
- `projects/autopark/data/processed/YYYY-MM-DD/*.json`
- `projects/autopark/runtime/reviews/YYYY-MM-DD/dashboard-quality.*`
- `projects/autopark/runtime/reviews/YYYY-MM-DD/post-publish-review.*`
- `projects/autopark/runtime/logs/YYYY-MM-DD-live-all-in-one.*`

Mirror:

- `%AUTOPARK_STATE_ROOT%\runs\YYYY-MM-DD\`

## Failure Policy

- 수집 일부 실패는 warn으로 남기고 계속 진행한다.
- 품질 gate fail은 Notion 발행을 막는다.
- 실행 실패는 로그와 state mirror를 보고 해당 step만 재시도한다.

## Test Cycle Scheduler

초기 테스트 단계에서는 매일 06:03 실행만으로 피드백이 너무 늦다. 다음 스크립트는 기본적으로
30분 간격, 12시간 동안 리허설을 반복한다. 기본 모드는 `--skip-publish`라 Notion을 갱신하지 않고
runtime/data/state mirror 산출물만 쌓는다.

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\install_autopark_test_schedule.ps1
```

발행까지 포함한 테스트가 필요하면 `-EnablePublish`를 붙인다. 이 경우에도 `AUTOPARK_PUBLISH_POLICY=gate`
기준을 따르므로 quality gate가 pass일 때만 같은 날짜 Notion 페이지를 갱신한다.

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\install_autopark_test_schedule.ps1 -IntervalMinutes 30 -DurationHours 12 -EnablePublish
```

테스트 태스크를 지울 때:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\install_autopark_test_schedule.ps1 -Unregister
```

Task Scheduler 등록 권한이 없는 세션에서는 현재 PowerShell 창에서 직접 루프를 띄운다.

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start_autopark_test_loop.ps1 -IntervalMinutes 30 -DurationHours 12
```
