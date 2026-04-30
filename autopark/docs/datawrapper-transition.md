# Datawrapper Transition

기준일: 2026-04-28

## Decision

`1. 시장은 지금`과 `3. 특징주 분석`의 고정 차트는 사이트 캡처 대신
API/구조화 데이터로 수집한 뒤 Datawrapper 차트로 제작한다.

스크린샷 파이프라인은 계속 유지하되, 역할을 아래로 낮춘다.

- 원본 화면 확인
- 장애/변경 감지
- 내부 시행착오 기록
- 사람이 판단할 때 보는 보조 증빙

Notion/방송 준비 문서에 우선 삽입할 산출물은 Datawrapper PNG/export 결과다.

## Reused Buykings Pattern

Buykings에는 이미 재사용 가능한 Datawrapper 운영 패턴이 있다.

- `scripts/datawrapper_publish.py`: JSON spec + prepared CSV를 Datawrapper에 업로드/발행
- `scripts/datawrapper_export_png.py`: chart id를 PNG로 export
- `scripts/export_wepoll_weekly_png.py`: export 후 로고 후처리 흐름
- `docs/chart-qc-checklist.md`: 방송/리포트용 차트 QC 기준
- `projects/wepoll-panic/charts/*.json`: Datawrapper chart spec 예시
- `projects/wepoll-panic/prepared/*.csv`: Datawrapper 입력 CSV 예시

Autopark는 별도 API 클라이언트부터 새로 만들지 않고, 위 스크립트를 호출하는 방식으로 시작한다.

## Target Flow

```text
market API fetch
-> normalized market CSV
-> Datawrapper spec 생성/갱신
-> scripts/datawrapper_publish.py
-> scripts/datawrapper_export_png.py
-> Autopark Notion page image block
```

스크린샷은 아래 경로에 내부 저장만 한다.

```text
autopark/runtime/screenshots/YYYY-MM-DD/
autopark/data/raw/YYYY-MM-DD/
```

## First Chart Set

### 1. 시장은 지금

- 미국 주요 지수 흐름: Dow / Nasdaq 100 / S&P 500 futures
- 미국 10년물 국채금리
- WTI / 브렌트
- 달러 인덱스 / 원달러
- 비트코인
- CNN 공포탐욕지수: API가 아니라 구조화 추출 또는 자체 gauge로 시작

### 3. 특징주 분석

- 특징주별 가격 흐름
- 특징주 등락률/거래량 표
- 필요 시 여러 티커를 한 장에 넣는 비교 차트

## Candidate Data Sources

초기 우선순위:

1. Yahoo Finance 계열 심볼
   - `ES=F`, `NQ=F`, `YM=F`
   - `CL=F`, `BZ=F`
   - `DX-Y.NYB`, `KRW=X`, `BTC-USD`
2. FRED
   - `DGS10` 등 금리 계열
3. Stooq
   - Yahoo Finance 장애 시 보조 historical data
4. CNN structured extract
   - 공포탐욕 latest/comparison 값
5. 유료/준유료 후보
   - Polygon, Nasdaq Data Link 등은 필요성이 생기면 검토

## Test Plan

### Phase 1. Local data fetch PoC

한 번에 다 붙이지 말고 아래 3개만 먼저 검증한다.

1. `us10y`
2. `crude-oil`
3. `ticker-price-action`

검증 기준:

- CSV가 날짜/값 컬럼으로 안정적으로 생성되는가
- 장 시작 전 시간대에도 최신 값 또는 직전 종가 기준을 설명할 수 있는가
- Datawrapper 차트로 올렸을 때 제목/축/범례가 방송용으로 읽히는가

### Phase 2. Datawrapper spec PoC

`autopark/charts/`에 chart spec을 만들고,
`autopark/prepared/`에 prepared CSV를 생성한다.

예상 명령:

```bash
autopark/.venv/bin/python autopark/scripts/prepare_datawrapper_inputs.py --list
autopark/.venv/bin/python autopark/scripts/fetch_market_chart_data.py --date 2026-04-28 --chart us10y
python3 scripts/datawrapper_publish.py autopark/charts/us10y-datawrapper.json
python3 scripts/datawrapper_export_png.py <chart_id> autopark/exports/current/us10y.png
```

### Phase 3. Notion 전환

4/22, 4/23 역구성 문서에서 `시장 캡처 이미지`를 바로 지우지는 않는다.
대신 같은 위치에 Datawrapper 산출물을 넣어 비교한다.

최종적으로는:

- Datawrapper PNG: Notion/방송 준비용
- 원본 스크린샷: 내부 증빙용

## Open Implementation Questions

- Yahoo Finance는 직접 HTTP 수집으로 충분한가, `yfinance` 의존성을 둘 것인가
- 장전/장중/장마감 중 어느 기준 시간을 차트 부제에 표시할 것인가
- 특징주 티커 목록은 문서별 수동 입력으로 둘지, 후보 생성 단계에서 자동 선택할지
- Datawrapper chart id를 날짜별로 새로 만들지, 고정 chart를 계속 update할지

## Current PoC Results

2026-04-28에 의존성 없는 Yahoo Finance chart API 수집 스크립트를 추가했다.

생성된 산출물:

- `autopark/prepared/us10y-2026-04-28.csv`
- `autopark/charts/us10y-datawrapper.json`
- `autopark/data/raw/2026-04-28/us10y-market-data.json`
- `autopark/prepared/crude-oil-2026-04-28.csv`
- `autopark/charts/crude-oil-datawrapper.json`
- `autopark/data/raw/2026-04-28/crude-oil-market-data.json`

검증:

- `prepare_datawrapper_inputs.py --list` 정상
- `fetch_market_chart_data.py --chart us10y` 정상
- `fetch_market_chart_data.py --chart crude-oil` 정상
- `scripts/datawrapper_publish.py --dry-run autopark/charts/us10y-datawrapper.json` 정상
- Datawrapper `us10y` chart 생성/게시 정상: `nofn2`
- `autopark/exports/current/us10y.png` PNG export 정상
- Notion `26.04.22` 페이지 하단에 Datawrapper 전환 테스트 블록 append 정상
- 2026-04-28에 `us10y`를 FRED-first로 전환했다.
  - source priority: `fred -> yahoo_finance`
  - FRED graph CSV는 `cosd`로 시작일을 제한하고, Python urllib timeout 시 `curl` fallback을 쓴다.
  - FRED 최신 관측일이 실행일보다 늦을 수 있으므로 부제는 실제 최신 관측일을 쓴다.
- 2026-04-28에 원유 차트도 FRED-first로 전환했다.
  - FRED series: `DCOILWTICO`, `DCOILBRENTEU`
  - 결측일은 전일 값으로 채우지 않고 해당 날짜 row를 제외한다.
  - 합산 비교 차트 `crude-oil`은 reference로 남기고, 운영용은 단독 차트 2장으로 분리한다.
  - WTI Datawrapper chart id: `TYqZk`, PNG export: `autopark/exports/current/crude-oil-wti.png`
  - Brent Datawrapper chart id: `jZDeO`, PNG export: `autopark/exports/current/crude-oil-brent.png`
- 2026-04-28에 `dollar-index`, `usd-krw`도 FRED-first로 전환했다.
  - FRED series: `DTWEXBGS`, `DEXKOUS`
  - Datawrapper chart ids: `aIYNm`, `tTyEQ`
  - PNG exports: `autopark/exports/current/dollar-index.png`, `autopark/exports/current/usd-krw.png`
  - 후속 개선에서 `dollar-index`는 FRED broad dollar index가 아니라 Yahoo Finance `DX-Y.NYB` 기반 `DXY`로 교체했다.
  - `us10y`, `crude-oil-wti`, `crude-oil-brent`, `dollar-index`, `usd-krw`는 Yahoo Finance 우선, FRED fallback으로 설정했다.
  - 2026-04-28 재생성 값:
    - US10Y: `26.04.28 현재 4.364%`
    - WTI: `26.04.28 현재 $99.83`
    - 브렌트: `26.04.28 현재 $104.57`
    - DXY: `26.04.28 현재 98.758`
    - 원/달러: `26.04.28 현재 1,473.85원`
- 2026-04-28에 `bitcoin`을 CoinGecko-first로 전환했다.
  - CoinGecko coin id: `bitcoin`
  - fallback: `yahoo_finance`
  - Datawrapper chart id: `87wAG`
  - PNG export: `autopark/exports/current/bitcoin.png`
- 2026-04-28에 경제캘린더를 Datawrapper table로 전환했다.
  - source: `https://ko.tradingeconomics.com/calendar?importance=2`
  - parser: `autopark/scripts/fetch_economic_calendar.py`
  - raw HTML: `autopark/data/raw/YYYY-MM-DD/tradingeconomics-calendar-importance2.html`
  - processed JSON: `autopark/data/processed/YYYY-MM-DD/economic-calendar.json`
  - prepared CSV: `autopark/prepared/economic-calendar-YYYY-MM-DD.csv`
  - Datawrapper chart id: `mPSRp`
  - PNG export: `autopark/exports/current/economic-calendar.png`
  - table columns: `시각`, `중요도`, `국가`, `이벤트`, `예상`
  - Datawrapper가 퍼센트 값을 숫자로 자동 반올림하지 않도록 `예상` 값을 텍스트로 강제한다.

## Current Datawrapper Assets

운영용 chart id:

- `nofn2`: 미국 10년물 국채금리
- `TYqZk`: WTI
- `jZDeO`: 브렌트
- `aIYNm`: 달러 지수
- `tTyEQ`: 원/달러
- `87wAG`: 비트코인
- `mPSRp`: 오늘의 경제 일정 table

현재 Notion에 넣는 PNG:

- `autopark/exports/current/us10y.png`
- `autopark/exports/current/crude-oil-wti.png`
- `autopark/exports/current/crude-oil-brent.png`
- `autopark/exports/current/dollar-index.png`
- `autopark/exports/current/usd-krw.png`
- `autopark/exports/current/bitcoin.png`
- `autopark/exports/current/economic-calendar.png`

주의:

- `^TNX`는 이미 퍼센트 값으로 내려오므로 별도 0.1 스케일을 적용하지 않는다.
- 현재 CSV는 Datawrapper line chart가 다루기 쉬운 wide format이다.
- 2026-04-28 PoC 이미지는 날짜별 본문 차트로 확정된 산출물이 아니라 업로드/렌더링 확인용이다.
