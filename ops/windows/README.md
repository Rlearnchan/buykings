# Windows Starter

이 폴더는 Windows 서버 PC에서 `buykings-morning`을 올릴 때
바로 참고하거나 실행할 수 있는 스타터 세트다.

현재 대상은 `wepoll-panic`과 `autopark`다.

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
- `start_autopark_chrome.ps1`
  - Autopark용 Chrome CDP 프로필 시작
- `run_autopark_daily.ps1`
  - 매일 06시대 Autopark Notion 대시보드 실행
- `smoke_test_autopark.ps1`
  - X/Finviz/Datawrapper/Notion dry-run smoke test

## Intended Use

권장 순서는 아래다.

1. Windows PC에서 `buykings`와 `wepoll-panic`를 GitHub에서 checkout
2. `ops/windows/codex-handoff.md`를 Codex에게 먼저 보여줌
3. Codex가 Python/Node/fetcher/environment를 세팅
4. smoke test 실행
5. Autopark Chrome 프로필에서 X, Finviz, Earnings Whispers, FedWatch, Polymarket 로그인/보안확인 1회 완료
6. 안정화 후 Task Scheduler 등록

## Important Note

이 세트는 `host fetcher + local Python compute` 기준이다.
즉 Docker 분리는 아직 포함하지 않는다.

## Autopark Daily

권장 Task Scheduler:

- Windows 로그인 사용자 세션에서 매일 `05:55 KST`: `ops\windows\start_autopark_chrome.ps1`
- 매일 `06:03 KST`: `ops\windows\run_autopark_daily.ps1`

Autopark는 기본적으로 `AUTOPARK_PUBLISH_POLICY=gate`를 사용한다. 품질 리뷰가
`pass`일 때만 Notion 날짜 페이지를 `replace-existing`으로 발행하고, 실패하면
Markdown/후보 장부/리뷰만 `AUTOPARK_STATE_ROOT\runs\YYYY-MM-DD\`에 보존한다.
