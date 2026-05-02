# Wepoll Codex Automation

Codex runs the Wepoll daily index job as an operator, not as the raw data collector.

## Schedule

- Time: every day at `00:30 KST`
- Target date: yesterday in Korea time
- Workspace: `C:\Users\User1\Documents\code\buykings`

## Daily Run

Codex should:

1. Check `http://127.0.0.1:8777/health`.
2. Run `.\.venv\Scripts\python.exe scripts\run_wepoll_daily_from_fetcher.py --target-date <YYYY-MM-DD>`.
3. Confirm `projects/wepoll-panic/state/appended_timeseries.csv` contains the target date.
4. Confirm Datawrapper publish output includes chart IDs `jRh1f` and `Dd29j`.

## Recovery Policy

If fetcher health fails, Codex should inspect the local process and port state, then restart the long-lived fetcher when possible. If authentication is expired, Codex should use the available browser/Computer Use workflow to restore the logged-in Wepoll session before retrying.

If download succeeds but compute fails, Codex should reuse the archived CSV from `runtime/downloads/wepoll` and rerun `scripts/run_wepoll_daily_append.py --target-date <YYYY-MM-DD>`. If Datawrapper publish fails, Codex should rerun only the publish step after verifying `DATAWRAPPER_ACCESS_TOKEN`.
