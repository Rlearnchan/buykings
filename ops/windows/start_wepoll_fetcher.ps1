$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ProfileDir = Join-Path $RepoRoot "runtime\wepoll-fetcher-profile"
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$NodeExe = "C:\Program Files\nodejs\node.exe"
$FetcherScript = Join-Path $RepoRoot "scripts\wepoll_fetcher_daemon.mjs"

Set-Location $RepoRoot

if (-not (Test-Path $ChromePath)) {
    throw "Chrome not found: $ChromePath"
}

if (-not (Test-Path $NodeExe)) {
    throw "Node not found: $NodeExe"
}

if (-not (Test-Path $FetcherScript)) {
    throw "Fetcher script not found: $FetcherScript"
}

& $NodeExe $FetcherScript `
  --user-data-dir $ProfileDir `
  --browser-path $ChromePath `
  --headed `
  --allow-manual-login `
  --verbose
