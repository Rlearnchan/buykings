# Wepoll Long-Lived Fetcher

기준일: 2026-04-21

이 문서는 위폴 다운로드를 `매번 새 브라우저 재실행`이 아니라
`로그인된 Playwright 브라우저를 오래 유지`하는 구조로 운영하는 방법을 정리한다.

이 방식은 네이버 소셜 로그인처럼

- 자동 로그인 구현이 까다롭고
- 저장된 세션이 새 실행에서 불안정할 수 있는

사이트에 더 적합하다.

## Why This Mode

우리가 실제로 확인한 점:

- Playwright 자체의 클릭/다운로드 제어는 가능하다.
- 문제는 "다음 실행에서도 로그인 상태가 유지되는가"였다.
- 전용 프로필 재실행만으로는 `login.php`로 튕겼다.

따라서 운영 본체를 아래처럼 바꾼다.

- Playwright가 전용 브라우저를 1회 띄운다.
- 사람이 그 브라우저에서 최초 로그인만 한다.
- 이후 브라우저 프로세스를 계속 유지한다.
- daily job은 로컬 HTTP endpoint를 호출해 다운로드만 지시한다.

즉 핵심은
`세션 재복구`가 아니라 `세션을 안 죽이는 것`이다.

## Process Model

### 1. Long-lived fetcher

Node + Playwright 프로세스가 계속 살아 있다.

역할:

- Chrome 전용 automation profile 유지
- 위폴 다운로드 페이지 세션 유지
- `/health`
- `/download`

### 2. Daily pipeline

기존 Python 배치가 담당한다.

역할:

- 위폴 raw CSV 다운로드 요청
- `scripts/run_wepoll_daily_append.py`
- Datawrapper publish
- PNG export + 로고
- Notion 갱신

### 3. Scheduler

Windows Task Scheduler 또는 서비스 관리자가 daily pipeline을 호출한다.

## Recommended Deployment Split

권장 분리:

- `wepoll-fetcher`: 장기 실행, GUI 세션 필요
- `daily-pipeline`: 단발 실행, Docker 가능

중요:

브라우저 로그인 세션을 유지해야 하므로 fetcher는 일반적인 headless batch 컨테이너보다
`로그인 가능한 데스크톱 세션`에 붙어 있는 것이 안전하다.

즉 첫 버전은 아래가 현실적이다.

- Windows PC에 fetcher를 로컬 프로세스로 상시 실행
- compute/publish만 Docker로 격리

## Startup Flow

### First boot

```bash
node scripts/wepoll_fetcher_daemon.mjs \
  --user-data-dir runtime/wepoll-fetcher-profile \
  --browser-path "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" \
  --headed \
  --allow-manual-login
```

이때 브라우저가 뜨면 사람이 네이버 로그인 1회만 진행한다.

로그인 완료 후에는 브라우저를 닫지 않는다.

### Health check

```bash
curl http://127.0.0.1:8777/health
```

정상 예시:

```json
{
  "ok": true,
  "authenticated": true,
  "page_url": "https://wepoll.kr/g2/bbs/mypage_data.php"
}
```

### Download request

```bash
curl -X POST http://127.0.0.1:8777/download \
  -H "Content-Type: application/json" \
  -d '{
    "periodLabel": "최근 3일",
    "boardLabel": "경제",
    "includeLabel": "글만",
    "formatLabel": "CSV",
    "outputDir": "runtime/downloads/wepoll"
  }'
```

## Daily Orchestration

daily 배치에서는 아래 순서로 쓴다.

1. fetcher `/health` 확인
2. fetcher `/download` 호출
3. 응답에서 내려준 CSV 경로 확보
4. `scripts/run_wepoll_daily_append.py --input <csv>`
5. PNG export + 로고
6. Notion 업데이트

## Failure Handling

### Session expired

증상:

- `/health`가 `authenticated: false`
- 또는 `/download`가 로그인 필요 에러 반환

대응:

- fetcher 프로세스는 유지
- 사람이 브라우저 창에서 다시 로그인
- 이후 다시 `/health` 확인

### Browser closed accidentally

대응:

- fetcher를 재시작
- 필요하면 1회 재로그인

### Download page changed

대응:

- fetcher 스크립트의 selector만 수정
- compute pipeline은 그대로 둔다

## Why Better Than Codex Control For This Job

이 구조의 장점:

- 토큰 기반 컴퓨터 제어를 계속 태우지 않는다.
- 재시도와 상태 확인이 API처럼 단순하다.
- 다운로드와 계산 파이프라인을 분리할 수 있다.
- 로그인만 사람 개입으로 남기고 나머지는 완전 자동화 가능하다.

Codex/Computer Use는 예외 상황 복구 도구로는 좋지만,
매일 반복 실행되는 fetcher 본체는 브라우저 전용 자동화가 더 적합하다.

## Near-Term Next Step

이 저장소 기준 다음 작업은 아래다.

1. `wepoll-fetcher`를 Windows 서버에서 실제 상시 실행
2. `daily-update` wrapper가 `/download`를 먼저 호출하도록 연결
3. Notion 갱신 스크립트 추가
