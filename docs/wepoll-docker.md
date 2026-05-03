# Wepoll daily Docker runbook

This runbook moves the Wepoll daily index automation into Docker while preserving the existing chart IDs `jRh1f` and `Dd29j`.

## Services

`wepoll-fetcher` keeps a long-lived Playwright browser profile at `.server-state/wepoll/fetcher-profile` and exposes the fetcher API on `http://127.0.0.1:8777`. The fetcher first tries the one-click Naver relogin path; if the session is fully expired, `/health` reports `authenticated: false` instead of creating new charts or continuing with a bad download. In the current Windows setup, the most reliable path is a hybrid run: keep the headed Windows fetcher on `127.0.0.1:8777` and run the daily compute/publish step in Docker via `host.docker.internal`.

`wepoll-daily` is a one-shot runner. It computes yesterday in `Asia/Seoul`, requests the exact target-date CSV path, appends the daily index, syncs SQLite, and publishes the existing Datawrapper charts unless `WEPOLL_SKIP_PUBLISH=1`. By default it calls the host headed fetcher at `http://host.docker.internal:8777`; set `WEPOLL_FETCHER_URL=http://wepoll-fetcher:8777` only when the containerized fetcher passes `/health` with `authenticated: true`.

`wepoll-daily-scheduler` runs the same one-shot script daily. By default it runs at `00:10` KST and retries at `00:30` only if the primary run failed.

## Commands

Start or verify the headed Windows fetcher:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\runtime\playwright-browsers"
node scripts\wepoll_fetcher_daemon.mjs --user-data-dir "$PWD\runtime\wepoll-fetcher-profile" --port 8777 --host 127.0.0.1 --headed --allow-manual-login --verbose
```

Optionally build and start the containerized fetcher:

```bash
docker compose -f docker-compose.wepoll.yml up -d --build wepoll-fetcher
```

Run one daily update for yesterday KST:

```bash
docker compose -f docker-compose.wepoll.yml run --rm wepoll-daily
```

Run a specific date:

```bash
docker compose -f docker-compose.wepoll.yml run --rm -e WEPOLL_TARGET_DATE=2026-05-02 wepoll-daily
```

Start the daily scheduler:

```bash
docker compose -f docker-compose.wepoll.yml up -d --build wepoll-fetcher wepoll-daily-scheduler
```

## Login recovery

The container cannot complete a brand-new interactive Naver login by itself. When `docker compose -f docker-compose.wepoll.yml exec wepoll-fetcher curl -fsS http://127.0.0.1:8777/health` returns `authenticated: false`, refresh the session in a headed/manual environment, then restart `wepoll-fetcher`. The mounted `.server-state/wepoll` directory preserves the browser profile between container restarts.
