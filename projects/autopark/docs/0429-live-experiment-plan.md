# 0429 Live Experiment Plan

기준일: 2026-04-28
대상 실험: 2026-04-29 아침방송 사전 대시보드 제작

## Goal

실제 `바이킹 0429.pptx`가 나오기 전에 Autopark가 먼저 04.29용 자료 후보, 선별 장부, 추천 스토리라인 3개를 만든다. 이후 실제 PPT와 대조해 “진행자가 고른 것”과 “우리가 골랐거나 놓친 것”의 차이를 학습한다.

핵심 질문은 하나다.

> 당일 후보 뉴스가 많았을 텐데, 왜 어떤 재료는 방송 서사가 되고 어떤 재료는 탈락했는가?

## Time Box

총 30분을 기준으로 한다.

| KST | 단계 | 산출물 |
|---:|---|---|
| 06:55 | preflight | 로그인/profile, `.env`, Datawrapper/OpenAI/Notion 키, 출력 폴더 확인 |
| 07:00 | collect | fast news, Batch B/X/리서치 차트, 경제일정, 시장 차트 데이터, 특징주 후보 |
| 07:10 | normalize/cluster | 중복 제거, hooks/tickers/source/time 정리, 후보 클러스터 |
| 07:15 | select | 스토리라인 3개, selected/reserve/rejected 후보 장부 |
| 07:25 | dashboard draft | Notion-ready Markdown 또는 내부 freeze pack |
| 07:30 | freeze | 이후 수정은 별도 `post-freeze`로 기록 |

## Run Commands

아래 명령은 `/Users/bae/Documents/code/buykings`에서 실행한다.

```bash
projects/autopark/.venv/bin/python projects/autopark/scripts/collect_today_misc.py --date 2026-04-29 --run-name today-misc-batch-a --overall-limit 80 --limit-per-source 15 --lookback-hours 24
projects/autopark/.venv/bin/python projects/autopark/scripts/collect_today_misc.py --date 2026-04-29 --batch-b-default --run-name today-misc-batch-b --overall-limit 80 --limit-per-source 12 --lookback-hours 36
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/collect_x_timeline.mjs --date 2026-04-29
projects/autopark/.venv/bin/python projects/autopark/scripts/build_visual_cards.py --date 2026-04-29
projects/autopark/.venv/bin/python projects/autopark/scripts/cluster_today_misc.py --date 2026-04-29 --limit-news 80 --limit-x 60 --limit-visuals 40
projects/autopark/.venv/bin/python projects/autopark/scripts/select_storylines_v4.py --date 2026-04-29 --selected-count 8 --max-candidates 24
projects/autopark/.venv/bin/python projects/autopark/scripts/build_live_experiment_pack.py --date 2026-04-29
```

시장 차트와 경제일정은 병렬로 갱신한다.

```bash
for chart in us10y crude-oil-wti crude-oil-brent dollar-index usd-krw bitcoin; do
  projects/autopark/.venv/bin/python projects/autopark/scripts/fetch_market_chart_data.py --date 2026-04-29 --chart "$chart" --collected-at "26.04.29 07:00"
done
projects/autopark/.venv/bin/python projects/autopark/scripts/fetch_economic_calendar.py --date 2026-04-29
```

특징주 일봉/Finviz 뉴스 출발점은 별도 캡처로 보강한다.

```bash
/Users/bae/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node projects/autopark/scripts/capture_finviz_feature_stocks.mjs --date 2026-04-29
projects/autopark/.venv/bin/python projects/autopark/scripts/build_feature_stock_cards.py --date 2026-04-29
```

## Freeze Outputs

주요 산출물:

- `projects/autopark/data/processed/2026-04-29/today-misc-batch-a-candidates.json`
- `projects/autopark/data/processed/2026-04-29/today-misc-batch-b-candidates.json`
- `projects/autopark/data/processed/2026-04-29/today-misc-clusters.json`
- `projects/autopark/data/processed/2026-04-29/storyline-selection-v4.json`
- `projects/autopark/data/processed/2026-04-29/live-experiment-pack.json`
- `projects/autopark/runtime/notion/2026-04-29/live-experiment-pack.md`

`live-experiment-pack`이 07:30 freeze 기준의 평가 원본이다. 실제 PPT가 나온 뒤에는 이 파일을 수정하지 않고, 별도 comparison 문서를 만든다.

## Selection Ledger Fields

각 후보는 최소 아래 필드를 가진다.

- `selection_status`: `selected`, `reserve`, `rejected`
- `storyline_fit`: 어느 후보 스토리라인 또는 클러스터에 붙는지
- `block_expandability`: 1장짜리 뉴스인지, 2-4장짜리 블록으로 커질 수 있는지
- `bridge_to_fixed_charts`: 금리/유가/달러/비트코인/히트맵과 연결되는지
- `bridge_to_tickers`: 실적/특징주 차트로 증명 가능한지
- `broadcast_hook`: 한국 아침 방송에서 바로 잡히는 훅인지
- `explanation_cost`: 배경 설명 비용
- `selection_reason`: 고른 이유
- `why_not_selected`: 보류/탈락 이유

## Evaluation After Actual PPT Arrives

실제 PPT가 나오면 아래 네 그룹으로 나눈다.

| 그룹 | 의미 | 다음 조치 |
|---|---|---|
| hit | PPT에 들어갔고 Autopark도 selected | 선별 규칙 유지 |
| low-ranked hit | PPT에 들어갔지만 Autopark는 reserve/rejected | 왜 낮게 봤는지 feature 수정 |
| miss | PPT에 들어갔지만 후보 풀에 없음 | source registry 또는 수집 방식 보강 |
| false positive | Autopark selected였지만 PPT에 없음 | 탈락 이유가 설명 가능한지 점검 |

평가 메모는 `projects/autopark/docs/0429-live-experiment-review.md`에 작성한다.

## Last Tweaks Before 07:00

1. `today_misc_sources.json`에서 Batch A/B source가 너무 적으면 빠른 뉴스 소스 1-2개를 추가 활성화한다.
2. X profile 로그인 상태를 06:55에 확인한다.
3. `select_storylines_v4.py` 모델은 비용 때문에 기본 `gpt-4.1-mini` 또는 환경변수 `AUTOPARK_SELECTOR_MODEL`로 고정한다.
4. Notion 발행은 실험 중에는 선택 사항이다. 평가 기준은 local freeze pack이다.
5. freeze 후에는 결과를 덮어쓰지 않는다. 재실행이 필요하면 `runtime/logs`에 이유를 남기고 post-freeze로 분리한다.
