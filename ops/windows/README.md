# Windows Starter

이 폴더는 Windows 서버 PC에서 `buykings-morning`을 올릴 때
바로 참고하거나 실행할 수 있는 스타터 세트다.

현재 1차 대상은 `wepoll-panic` 하나다.

## Included Files

- [codex-handoff.md](/Users/bae/Documents/code/buykings/ops/windows/codex-handoff.md)
  - Windows PC의 Codex가 먼저 읽으면 되는 handoff 문서
- [server.env.example](/Users/bae/Documents/code/buykings/ops/windows/server.env.example)
  - 서버용 환경 변수 예시
- [start_wepoll_fetcher.ps1](/Users/bae/Documents/code/buykings/ops/windows/start_wepoll_fetcher.ps1)
  - long-lived fetcher 시작 예시
- [run_buykings_morning.ps1](/Users/bae/Documents/code/buykings/ops/windows/run_buykings_morning.ps1)
  - 상위 morning runner 실행 예시
- [smoke_test_wepoll.ps1](/Users/bae/Documents/code/buykings/ops/windows/smoke_test_wepoll.ps1)
  - fetcher health / download / morning job smoke test

## Intended Use

권장 순서는 아래다.

1. Windows PC에서 `buykings`와 `wepoll-panic`를 GitHub에서 checkout
2. `ops/windows/codex-handoff.md`를 Codex에게 먼저 보여줌
3. Codex가 Python/Node/fetcher/environment를 세팅
4. smoke test 실행
5. 안정화 후 Task Scheduler 등록

## Weekly Publish Rule

`wepoll-panic`은 매일 데이터를 append하지만, 발간용 Datawrapper chart는 주차 단위로 관리한다.

- 주중(화~일): 같은 주차 chart를 계속 update
- 월요일 데이터가 처음 반영될 때: 새 주차 chart pair를 생성
- 새 pair는 `projects/wepoll-panic/charts/weekly-timeseries-YYYY-MM-DD.json`
- 새 pair는 `projects/wepoll-panic/charts/weekly-bubble-YYYY-MM-DD.json`

예를 들어 `2026-04-20` 월요일 데이터가 들어오면:

- `weekly-timeseries-2026-04-20.json`
- `weekly-bubble-2026-04-20.json`

이 새 spec이 만들어지고, Datawrapper에도 새 chart 두 개가 생성된다.
그 주의 나머지 날은 같은 chart id를 재사용한다.

## Task Scheduler

권장 구성:

1. 로그인 사용자 세션에서 `start_wepoll_fetcher.ps1` 상시 실행
2. Task Scheduler에서는 `run_buykings_morning.ps1`만 호출

예시:

- Program/script: `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`
- Add arguments: `-ExecutionPolicy Bypass -File C:\Users\User1\Documents\code\buykings\ops\windows\run_buykings_morning.ps1`
- Start in: `C:\Users\User1\Documents\code\buykings`

권장 트리거:

- 매일 오전 11:35
- 실행 계정은 fetcher를 띄워 둔 같은 Windows 사용자
- "Run only when user is logged on" 사용
- 실패 시 5~10분 간격으로 2~3회 재시도

## Current Windows Defaults

현재 Windows 이관 기준 기본값:

- second pass backend: `openai`
- second pass model: `gpt-5-mini`
- `WEPOLL_PANIC_ROOT`: `vendor\wepoll-panic`

## Important Note

이 세트는 `host fetcher + local Python compute` 기준이다.
즉 Docker 분리는 아직 포함하지 않는다.
