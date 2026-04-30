# Capture Status

기준일: 2026-04-27

`scripts/capture_source.mjs`로 고정 소스 일부를 실제 캡처해 본 결과다.

## Role Change

2026-04-28부터 `1. 시장은 지금`과 `3. 특징주 분석`의 고정 차트는
API/구조화 데이터로 수집해 Datawrapper에서 제작하는 것을 기본으로 한다.

이 문서의 캡처 파이프라인은 계속 유지하지만, 역할은 아래로 제한한다.

- 원본 화면 확인
- 사이트 레이아웃/접근 장애 감지
- 내부 시행착오 기록
- Datawrapper로 만들 수 없는 일회성 화면 증빙

Notion/방송 준비 문서에 우선 넣을 이미지는 `projects/autopark/exports/current/`의
Datawrapper export 결과로 전환한다.

## Summary

| Source | Status | Output | Notes |
| --- | --- | --- | --- |
| `cnn-fear-greed` | `ok` | `runtime/screenshots/2026-04-27/cnn-fear-greed.png` | 정상 캡처. viewport 캡처가 적합해서 `capture_full_page=false` 적용. |
| `cnbc-us10y` | `ok` | `runtime/screenshots/2026-04-27/cnbc-us10y.png` | 정상 캡처. 제목에 금리 값이 들어와 추후 수치 추출 가능. |
| `finviz-index-futures` | `ok` | `runtime/screenshots/2026-04-27/finviz-index-futures.png` | `finviz` persistent profile 재사용으로 정상 캡처. |
| `finviz-sp500-heatmap` | `ok` | `runtime/screenshots/2026-04-27/finviz-sp500-heatmap.png` | `finviz` persistent profile bootstrap 후 정상 캡처. |
| `investing-wti` | `partial` | `runtime/screenshots/2026-04-27/investing-wti.png` | 본문/가격은 로드되나 TradingView chart iframe이 비어 있음. |
| `cme-fedwatch` | `error` | metadata only | `ERR_HTTP2_PROTOCOL_ERROR` before page load. |

## Interpretation

초기 자동화 가능:

- CNN Fear & Greed
- CNBC US10Y

별도 전략 필요:

- Finviz 계열
- Investing.com 계열
- CME FedWatch

Finviz와 Investing은 headless Chromium에서 보안 검증 페이지가 떴다.
1차 해결책은 headed Chrome + persistent profile이다. 사이트별 정상 브라우저
세션을 한 번 만들어 두고, 이후 캡처는 같은 profile의 쿠키/세션을 재사용한다.
이 방식은 X처럼 로그인이 필수인 소스에도 같은 운영 모델을 적용할 수 있다.

2026-04-27 검증 결과:

- Finviz: `finviz` profile로 보안 검증을 통과했고, 히트맵과 메인 지수 흐름 모두 정상 캡처.
- Investing.com: `investing` profile로 로그인/본문 로드는 가능하지만, 차트 제공 iframe이 비어 있어 `partial` 처리. 이 경우 방송용 차트 캡처로는 실패로 본다.

프로필 이름:

- `finviz`
- `investing`
- `x`

Bootstrap 예시:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source finviz-sp500-heatmap --bootstrap --browser-channel chrome --bootstrap-wait-ms 180000
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source investing-wti --bootstrap --browser-channel chrome --bootstrap-wait-ms 180000
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source earnings-whispers-x --bootstrap --browser-channel chrome --bootstrap-wait-ms 300000
```

재사용 예시:

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_source.mjs --source finviz-sp500-heatmap --use-auth-profiles --headed --browser-channel chrome
```

CME는 보안 검증이 아니라 HTTP/2 네비게이션 오류이므로, URL 지역 설정 변경,
브라우저 channel 변경, headed 실행, 또는 API/정적 데이터 대체 가능성을 따로 본다.

## Next Capture Targets

1. `cnbc-us10y`에서 title/DOM 텍스트로 금리 값을 JSON 필드에 추출
2. `cnn-fear-greed`에서 지수 값과 상태를 JSON 필드에 추출
3. Finviz/Investing/X headed persistent profile bootstrap
4. 성공 소스만 묶어 실행하는 batch collector 추가

## Batch Collector

`scripts/capture_batch.mjs --section market_now`는 기본적으로
`known_capture_issue`가 없는 enabled source만 실행한다.

2026-04-27 검증된 기본 batch 대상:

- `cnbc-us10y`
- `cnn-fear-greed`

실행 결과:

- `ok=true`
- 두 소스 모두 `status=ok`

## Extracted Fields

`scripts/capture_source.mjs`는 캡처와 함께 일부 source의 핵심 숫자를
`data/raw/YYYY-MM-DD/<source>.json`의 `extracted` 필드에 저장한다.

현재 추출 가능:

- `cnbc-us10y`
  - `extracted.quote.symbol`
  - `extracted.quote.yield_pct`
  - `extracted.quote.change`
  - `extracted.quote.change_pct`
  - `extracted.quote.quote_time`
  - `extracted.quote.yield_open_pct`
  - `extracted.quote.yield_day_high_pct`
  - `extracted.quote.yield_day_low_pct`
  - `extracted.quote.yield_prev_close_pct`
- `cnn-fear-greed`
  - `extracted.fear_greed.score`
  - `extracted.fear_greed.status`
  - `extracted.fear_greed.updated_at_text`

추가 검토:

- CNN의 previous close / 1 week / 1 month / 1 year 비교값은 화면에는 보이지만
  DOM 텍스트에서 안정적으로 추출되지 않아 현재 `null`일 수 있다.
- Investing 계열은 본문 가격 수치는 사용할 수 있으나 차트 캡처는 TradingView iframe
  렌더링 문제 때문에 대체 URL 또는 자체 차트 생성 검토가 필요하다.

## Processed Outputs

`scripts/build_morning_inputs.mjs --date 2026-04-27`는 raw metadata를 아래 내부 산출물로 묶는다.

- `data/processed/2026-04-27/morning_inputs.json`
- `runtime/notion/2026-04-27/26.04.27.md`

2026-04-27 생성 Markdown은 테스트 페이지로 한 번 게시했으나,
운영 방침에 맞지 않아 archive 처리했다. 시행착오 및 단계별 결과는
이 문서와 로컬 산출물에만 남긴다.

- archived page: https://www.notion.so/26-04-27-34f468fb878d81618714da7611215ace
