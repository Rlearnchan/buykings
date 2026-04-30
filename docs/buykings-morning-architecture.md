# Buykings Morning Architecture

기준일: 2026-04-21

이 문서는 `buykings-morning`을 최상단 오케스트레이터로 두고,
그 아래에 여러 작업 트랙을 붙여 나가는 구조를 정리한다.

## Top-Level Idea

`buykings-morning`은 하나의 개별 분석 job이 아니라,
아침에 돌아야 하는 여러 job을 묶는 상위 엔트리포인트다.

현재 붙는 첫 작업:

- `wepoll-panic`

앞으로 붙일 작업:

- `capture-and-collect`
- 기타 경제 사이트 캡처/수집
- 필요 시 morning summary 조립
- 나중에 Notion 업데이트

## Design Principle

상위 계층은 orchestration만 담당한다.

- job 순서 관리
- enabled/disabled 관리
- 실행 결과 집계
- 실패 지점 식별

하위 계층은 각 작업의 도메인 로직을 담당한다.

- `wepoll-panic`: 위폴 다운로드, 지수 산출, Datawrapper
- `capture-and-collect`: 외부 사이트 캡처/수집
- future jobs: 별도 command/script

## Current Files

### Manifest

- [buykings-morning.json](/Users/bae/Documents/code/buykings/config/buykings-morning.json)

역할:

- 어떤 job이 상위 morning에 포함되는지 정의
- enabled 상태 정의
- 실행 command 정의

### Runner

- [run_buykings_morning.py](/Users/bae/Documents/code/buykings/scripts/run_buykings_morning.py)

역할:

- manifest를 읽는다
- enabled job만 순서대로 실행한다
- stdout/stderr/exit code를 모아 JSON으로 출력한다

## Current Job Tree

### buykings-morning

- `wepoll-panic`
- `capture-and-collect` (placeholder)
- `other-morning-jobs` (placeholder)

## Why This Shape

이 구조의 장점:

- 새 작업을 붙일 때 상위 scheduler를 다시 짤 필요가 없다.
- 각 작업이 독립적으로 실패해도 어디서 깨졌는지 바로 보인다.
- 나중에 Docker Compose, Task Scheduler, cron 중 무엇으로 감싸도 내부 job 구조는 유지된다.

## Recommended Runtime Split

### Layer 1. Long-lived fetchers

브라우저 로그인 세션이 필요한 작업은 별도 장기 실행 프로세스로 둔다.

예:

- `wepoll-fetcher`

### Layer 2. Morning runner

상위 runner는 장기 실행 fetcher나 배치 스크립트를 호출한다.

예:

- `python3 scripts/run_buykings_morning.py`

### Layer 3. Scheduler

Windows Task Scheduler나 다른 외부 scheduler가 상위 runner를 호출한다.

## Example Flow

현재 morning 실행 예시는 아래처럼 해석하면 된다.

1. `buykings-morning` 시작
2. `wepoll-panic` job 실행
3. 내부적으로 `run_wepoll_daily_from_fetcher.py` 호출
4. fetcher에서 raw CSV 다운로드
5. daily append / Datawrapper / SQLite sync 수행
6. 상위 runner가 결과 JSON 집계

현재 `wepoll-panic`은 가장 먼저 서버로 옮길 수 있는 대상이고,
그 기준 문서는 [wepoll-panic-migration.md](/Users/bae/Documents/code/buykings/docs/wepoll-panic-migration.md)에 따로 정리했다.

## Next Expansion

다음에 붙일 때는 아래 원칙을 따른다.

### capture-and-collect

- 개별 script를 먼저 만든다
- script 하나로 성공/실패가 분명하게 끝나게 한다
- manifest에 새 job으로 붙인다

### Notion

지금은 상위 구조에만 자리를 남겨두고,
실제 Notion page update는 나중에 별도 job으로 붙인다.

예:

- `notion-morning-refresh`

## Example Commands

전체 job 목록 확인:

```bash
python3 scripts/run_buykings_morning.py --list
```

현재 enabled job 실행:

```bash
python3 scripts/run_buykings_morning.py
```

특정 job만 실행:

```bash
python3 scripts/run_buykings_morning.py --job wepoll-panic
```
