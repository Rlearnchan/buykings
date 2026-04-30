# Codex Handoff For Windows Server

이 문서는 Windows 서버 PC의 Codex가 `wepoll-panic`과 `autopark` 마이그레이션을 이어받을 때
가장 먼저 읽는 스타터 문서다.

## Mission

이번 턴의 목표는 두 가지다.

1. `buykings-morning` 아래 `wepoll-panic`을 Windows 서버에서 실행 가능하게 유지하기
2. `autopark`가 매일 KST 06시대에 Notion 대시보드를 gate 기반으로 발행하게 만들기

아직 하지 않을 것:

- `capture-and-collect`
- Docker compute 분리
- API delivery 고도화

## Source Of Truth

먼저 아래 문서를 읽는다.

1. [wepoll-panic-migration.md](/Users/bae/Documents/code/buykings/docs/wepoll-panic-migration.md)
2. [wepoll-windows-server-runbook.md](/Users/bae/Documents/code/buykings/docs/wepoll-windows-server-runbook.md)
3. [buykings-morning-architecture.md](/Users/bae/Documents/code/buykings/docs/buykings-morning-architecture.md)
4. [wepoll-long-lived-fetcher.md](/Users/bae/Documents/code/buykings/docs/wepoll-long-lived-fetcher.md)
5. `projects/autopark/docs/autopark-operating-runbook.md`
6. `projects/autopark/docs/source-playbook.md`
7. `projects/autopark/docs/notion-dashboard-layout.md`

## Repo Layout To Aim For

권장 레이아웃:

```text
C:\ops\
  buykings\
  wepoll-panic\
```

`buykings`는 기본적으로 sibling 경로의 `..\wepoll-panic`를 찾는다.

## GitHub Assumption

현재 맥 로컬의 `buykings`는 GitHub 원격이 연결돼 있다.

- `https://github.com/Rlearnchan/buykings.git`

Windows 서버에서는 가능하면 두 레포를 GitHub에서 fresh clone/pull로 맞춘다.
로컬 복사보다 GitHub를 source of truth로 우선한다.

만약 `wepoll-panic`가 아직 GitHub 기준으로 정리되지 않았다면:

- 일단 `buykings`만 GitHub에서 clone
- `wepoll-panic`는 별도 전달본 또는 GitHub checkout으로 배치
- 최종적으로는 sibling 구조만 맞춘다

## What Already Works

이미 준비된 것:

- `scripts/wepoll_fetcher_daemon.mjs`
- `scripts/run_wepoll_daily_from_fetcher.py`
- `scripts/run_wepoll_daily_append.py`
- `scripts/run_wepoll_panic_daily_batch.py`
- `scripts/run_buykings_morning.py`
- `config/buykings-morning.json`
- `projects/autopark/scripts/run_live_dashboard_all_in_one.py`
- `ops/windows/start_autopark_chrome.ps1`
- `ops/windows/run_autopark_daily.ps1`
- `ops/windows/smoke_test_autopark.ps1`

중요한 구조:

- fetcher: 로그인된 브라우저를 장기 실행
- daily append: fetcher에서 CSV를 받아 계산
- morning runner: 상위 job orchestration

## First Tasks

Windows PC의 Codex는 아래 순서로 진행하면 된다.

1. `buykings` clone/pull 상태 확인
2. `wepoll-panic` clone/pull 또는 배치 상태 확인
3. Python venv 생성
4. `npm install`
5. `.env` 준비
6. fetcher headed 실행
7. `/health` 확인
8. `smoke_test_wepoll.ps1` 또는 개별 명령으로 검증
9. `start_autopark_chrome.ps1` 실행
10. Chrome 프로필에서 X, Finviz, Earnings Whispers, FedWatch, Polymarket 로그인/보안확인
11. `smoke_test_autopark.ps1` 실행
12. Task Scheduler에 `run_autopark_daily.ps1`를 매일 `06:03 KST`로 등록

## Preferred Commands

### Fetcher boot

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start_wepoll_fetcher.ps1
```

### Morning run

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\run_buykings_morning.ps1
```

### Smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\smoke_test_wepoll.ps1
```

### Autopark Chrome boot

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start_autopark_chrome.ps1
```

### Autopark daily run

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\run_autopark_daily.ps1
```

### Autopark smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\smoke_test_autopark.ps1
```

## Decision Rules

- 로그인 자동화보다 로그인 세션 유지가 우선이다.
- `wepoll-fetcher`는 Windows 사용자 세션에서 살아 있어야 한다.
- Autopark Chrome CDP 프로필도 Windows 사용자 세션에서 유지한다.
- Autopark는 `AUTOPARK_PUBLISH_POLICY=gate`가 기본이며, 품질 gate가 pass일 때만 Notion 발행한다.
- 첫 이관에서는 Docker보다 로컬 실행 단순성을 우선한다.
- GitHub로 해결 가능한 차이는 GitHub pull/update를 우선 사용한다.
- `buykings-morning` 상위 구조는 유지하고, `wepoll-panic`만 먼저 안정화한다.

## Done Condition

이번 1차 handoff의 완료 기준:

1. fetcher가 Windows에서 실행된다
2. 사람이 1회 로그인 후 `/health`가 `authenticated: true`를 반환한다
3. `run_wepoll_daily_from_fetcher.py`가 raw CSV 다운로드에 성공한다
4. `wepoll-panic` daily compute가 실행된다
5. 필요 시 `run_buykings_morning.py --job wepoll-panic`로 같은 결과를 재현할 수 있다
6. `smoke_test_autopark.ps1`가 X/Finviz/Datawrapper/Notion dry-run을 통과한다
7. `run_autopark_daily.ps1`가 Markdown, 품질 리뷰, post-publish review, state mirror를 만든다
