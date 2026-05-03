# Buykings

Buykings는 방송 준비와 운영 자료를 자동으로 모으고 발행하기 위한 작업 저장소입니다.

현재 중심 프로젝트는 두 가지입니다.

- `projects/autopark`: 매일 아침 시장/뉴스/차트 자료를 모아 Notion 방송 대시보드를 발행합니다.
- `projects/wepoll-panic`: 위폴 데이터 수집, 누적, Datawrapper 차트 갱신을 담당합니다.

## Main Automations

| Automation | Compose file | Main services | Purpose |
| --- | --- | --- | --- |
| Autopark morning dashboard | `docker-compose.autopark.yml` | `autopark-browser`, `autopark-publisher` | 시장 자료 수집, 차트 캡처, LLM 해석, Notion 발행 |
| Autopark retrospective | `docker-compose.autopark.yml` | `autopark-retrospective` | 방송 후 YouTube/위폴 회고 자료 생성 |
| Wepoll daily update | `docker-compose.wepoll.yml` | `wepoll-daily-scheduler`, `wepoll-fetcher` | 위폴 원천 데이터 수집과 차트 갱신 |

상태 확인:

```powershell
docker compose -f docker-compose.autopark.yml ps
docker compose -f docker-compose.wepoll.yml ps
docker logs --tail 80 buykings-autopark-publisher
docker logs --tail 80 buykings-autopark-retrospective
docker logs --tail 80 buykings-wepoll-daily-scheduler
```

재기동:

```powershell
docker compose -f docker-compose.autopark.yml up -d --build autopark-browser autopark-publisher autopark-retrospective
docker compose -f docker-compose.wepoll.yml up -d --build wepoll-daily-scheduler
```

## Autopark At A Glance

Autopark의 전체 흐름은 아래와 같습니다.

```text
scheduled Docker run
  -> browser/CDP and collection
  -> chart export
  -> market radar
  -> evidence microcopy
  -> market focus
  -> editorial brief
  -> compact dashboard render
  -> quality gate
  -> Notion publish
```

더 자세한 설명은 `projects/autopark/README.md`를 보세요.

## Repository Layout

```text
.
|-- docker-compose.autopark.yml
|-- docker-compose.wepoll.yml
|-- ops/
|-- scripts/
|-- projects/
|   |-- autopark/
|   `-- wepoll-panic/
|-- docs/
|-- exports/
|-- runtime/
`-- db/
```

## What Should Be Committed

Commit candidates:

- source code and scripts
- tests
- stable config
- operating docs, sourcebooks, rehearsal reports
- intentional chart spec changes

Usually keep out of Git:

- API keys and `.env`
- raw collection data
- generated runtime logs/screenshots
- exported current images
- browser profiles
- large raw PPT/PDF/RTF reference files

Before committing:

```powershell
git status --short
python -m unittest discover -s projects/autopark/tests
```
