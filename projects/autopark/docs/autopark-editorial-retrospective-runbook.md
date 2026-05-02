# Autopark Editorial And Retrospective Runbook

기준일: 2026-05-02

이 문서는 Autopark의 LLM 편집장 단계, FedWatch 분할 표, 방송 후 회고 루프를 운영하기 위한 내부 기준이다.

## Daily Loop

매일 운영은 두 번 돈다.

아침 루틴은 05:00에 시작해 05:30까지 Notion 대시보드 발행을 끝내는 것이 목표다. 07:20 방송 시작 전에 진행자가 실제 자료를 만들 시간을 확보해야 하기 때문이다. 이때 `run_live_dashboard_all_in_one.py`가 수집, Datawrapper 발행, `market-radar`, `editorial-brief`, Notion Markdown, 품질검수, Notion 게시를 순서대로 실행한다.

방송 후 루틴은 위폴 유튜브 라이브 다시보기의 한국어 자동 자막이 생성된 뒤 실행한다. 보통 방송 종료 후 몇 시간 안에 자막이 뜨지만, 지연될 수 있으므로 여러 번 재시도한다. 이 루틴은 실제 진행자 구간과 아침 대시보드를 비교해 회고록을 만들고, 다음날 편집장 단계가 읽을 `retrospective-feedback.md`를 남긴다.

## Morning Editorial Brief

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\build_editorial_brief.py --date YYYY-MM-DD
```

입력:

- `data/processed/YYYY-MM-DD/market-radar.json`
- `data/processed/YYYY-MM-DD/finviz-feature-stocks.json`
- `data/processed/YYYY-MM-DD/visual-cards.json`
- 최근 7일 `editorial-brief.json`
- 최근 7일 `runtime/broadcast/*/retrospective-feedback.md`

출력:

- `data/processed/YYYY-MM-DD/editorial-brief.json`

정책:

- 좋은 후보가 3개면 3개만 쓴다.
- 5개를 억지로 채우지 않는다.
- 각 스토리라인은 추천도 별 1-3개, 훅, 왜 지금, 핵심 주장, 쓸 자료, 버릴 자료, 방송 멘트 초안, 반론을 가진다.
- 내부 점수, 클러스터, 소스 개수 로직은 사용자에게 보이는 문장에 노출하지 않는다.
- `evidence_to_use`는 반드시 당일 후보 `item_id`를 참조해야 한다.

Fallback:

OpenAI API 키가 없거나 API/JSON/schema 오류가 나면 기존 `market-radar.json` 기반 fallback brief를 만든다. 이 경우 전체 파이프라인은 계속 진행하지만, `fallback=true`와 사유가 기록된다.

## Notion Rendering

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\build_live_notion_dashboard.py --date YYYY-MM-DD
```

상단 구조:

1. 오늘의 핵심 질문
2. 추천 스토리라인
3. 자료 수집

`editorial-brief.json`이 valid이고 fallback이 아니면 추천 스토리라인은 이 파일을 우선 사용한다. 없거나 invalid이면 기존 `market-radar.json` storylines로 fallback한다.

## FedWatch Split Tables

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\prepare_fedwatch_datawrapper_splits.py --date YYYY-MM-DD
```

역할:

`prepared/fedwatch-conditional-probabilities-YYYY-MM-DD.csv`를 행 기준 반반으로 나누어 단기/장기 표를 만든다. 13개 회의일이면 단기 7행, 장기 6행으로 나뉜다.

산출물:

- `prepared/fedwatch-conditional-probabilities-short-term-YYYY-MM-DD.csv`
- `prepared/fedwatch-conditional-probabilities-long-term-YYYY-MM-DD.csv`
- `charts/fedwatch-conditional-probabilities-short-term-datawrapper.json`
- `charts/fedwatch-conditional-probabilities-long-term-datawrapper.json`
- `exports/current/fedwatch-conditional-probabilities-short-term.png`
- `exports/current/fedwatch-conditional-probabilities-long-term.png`

표현 기준:

- 제목은 `FedWatch 단기 금리확률`, `FedWatch 장기 금리확률`이다.
- 부제에는 `현재 기준금리 3.50-3.75%`처럼 현재 기준금리를 둔다.
- 컬럼명에는 `(현재)`를 붙이지 않는다.
- 회의일은 `26.06.17`처럼 짧게 보이게 한다.
- Datawrapper 정렬을 위해 CSV 값은 `26.06.17@@20260617` 형식을 쓴다.
- 히트맵은 `0 = 흰색`, `100 = 부드러운 코랄` 연속형으로 둔다.
- 상단 레전드는 노출하지 않는다.

Datawrapper table heatmap 주의점:

컬럼 설정에는 boolean이 아니라 object를 쓴다.

```json
"heatmap": {
  "enabled": true
}
```

## Quality Gate

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\review_dashboard_quality.py --date YYYY-MM-DD --json
```

검사 항목:

- 필수 섹션 존재
- 추천 스토리라인 3개 이상
- 제목 중복 없음
- 추천도 누락 없음
- `hook`, `why_now`, `talk_track` 누락 없음
- `evidence_to_use` 없는 주장 경고
- 같은 근거 item의 과도한 반복 경고
- 내부 로직 문장 노출 감점
- 이미지/표 존재
- 영어 원문 제목이 과하게 노출되는지 확인

품질 gate가 pass이면 Notion 발행을 진행한다. fail이면 로컬 산출물만 남긴다.

## Post-Broadcast Transcript Fetch

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\fetch_wepoll_transcript.py --date YYYY-MM-DD
```

기본 동작:

- `https://www.youtube.com/@wepoll_original/streams`에서 당일 업로드 라이브를 찾는다.
- 당일 `upload_date`가 맞는 영상만 사용한다.
- 당일 영상이 없으면 `video_not_found`를 기록하고 종료한다.
- 한국어 수동 자막을 먼저 받고, 없으면 자동 생성 한국어 자막을 받는다.
- 자막이 아직 없으면 `transcript_unavailable`을 기록하고 재시도를 기다린다.
- 초반 40분만 `host-segment.md`로 저장한다.

수동 override:

```powershell
.\.venv\Scripts\python.exe projects\autopark\scripts\fetch_wepoll_transcript.py --date YYYY-MM-DD --video-url YOUTUBE_URL
```

`--allow-nearest`는 당일 영상이 없을 때 가장 최근 종료된 영상을 쓰는 옵션이다. 과거 버디버디 영상이 잘못 들어갈 수 있으므로 기본 운영에서는 쓰지 않는다.

## Broadcast Retrospective

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\build_broadcast_retrospective.py --date YYYY-MM-DD
```

입력:

- `runtime/notion/YYYY-MM-DD/YY.MM.DD.md`
- `data/processed/YYYY-MM-DD/editorial-brief.json`
- `data/processed/YYYY-MM-DD/market-radar.json`
- `runtime/broadcast/YYYY-MM-DD/host-segment.md`

출력:

- `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.md`
- `runtime/reviews/YYYY-MM-DD/broadcast-retrospective.json`
- `runtime/broadcast/YYYY-MM-DD/retrospective-feedback.md`

회고 항목:

- 추천 스토리라인 적중률
- 실제 방송에 쓰였지만 대시보드가 놓친 주제
- 대시보드에는 있었지만 방송에서 쓰이지 않은 자료
- 포맷 오류와 수정안
- 소스별 유용도
- 다음날 프롬프트 업데이트 후보
- 코드/운영 개선 후보

중요 원칙:

회고는 자동 코드 수정이 아니다. 프롬프트, 소스 가중치, 코드 수정 후보를 제안하지만 직접 소스 코드를 고치지는 않는다. 코드 변경은 별도 Codex 작업으로 검토 후 적용한다.

## Combined Post-Broadcast Runner

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\run_broadcast_retrospective.py --date YYYY-MM-DD --attempts 6 --sleep-minutes 60
```

권장 자동화:

- 10:30 KST부터 실행
- 60분 간격, 최대 6회 재시도
- 자막이 없으면 대기 상태만 기록
- 자막이 있으면 회고까지 생성

## Weekly Review

스크립트:

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe projects\autopark\scripts\review_editorial_week.py --end-date YYYY-MM-DD --days 7
```

출력:

- `runtime/weekly/YYYY-Www/source-value-report.md`
- `runtime/weekly/YYYY-Www/storyline-repeat-report.md`
- `runtime/weekly/YYYY-Www/prompt-improvement-notes.md`

이 리포트는 7일 동안 많이 수집됐지만 거의 쓰이지 않는 소스, 자주 쓰이지만 오판 가능성이 큰 소스, 반복되는 AI/유가/실적/Fed 프레임을 점검한다.

## Manual Review Checklist

아침 발행 후:

- Notion 상단 핵심 질문이 당일 자료와 맞는가.
- 추천 스토리라인이 실제 방송 꼭지처럼 읽히는가.
- FedWatch 단기/장기 표가 잘리지 않고 들어갔는가.
- Finviz 캡처가 잘리지 않았는가.
- 내부 점수/클러스터 설명이 노출되지 않았는가.

방송 회고 후:

- 실제 진행자가 쓴 소재가 `used_storylines` 또는 `missed_broadcast_topics`에 반영됐는가.
- `retrospective-feedback.md`가 너무 원문 자막 중심이 아니라 운영 가능한 피드백으로 요약됐는가.
- 다음날 편집장 프롬프트에 반영할 만한 내용이 있는가.
