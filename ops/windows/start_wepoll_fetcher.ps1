$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ProfileDir = Join-Path $RepoRoot "runtime\wepoll-fetcher-profile"
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

Set-Location $RepoRoot

if (-not (Test-Path $ChromePath)) {
    throw "Chrome not found: $ChromePath"
}

npm run wepoll:fetcher -- `
  --user-data-dir $ProfileDir `
  --browser-path $ChromePath `
  --headed `
  --allow-manual-login `
  --verbose
