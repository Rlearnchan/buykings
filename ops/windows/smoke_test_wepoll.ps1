$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FetcherUrl = "http://127.0.0.1:8777/health"

Set-Location $RepoRoot

if (-not (Test-Path $PythonExe)) {
    throw "Python venv executable not found: $PythonExe"
}

Write-Host "[1/3] Checking fetcher health"
Invoke-RestMethod -Uri $FetcherUrl -Method Get | ConvertTo-Json -Depth 5

Write-Host "[2/3] Download-only smoke test"
& $PythonExe "scripts/run_wepoll_daily_from_fetcher.py" `
  --skip-append `
  --skip-sqlite-sync

Write-Host "[3/3] Morning job smoke test"
& $PythonExe "scripts/run_buykings_morning.py" `
  --job "wepoll-panic"
