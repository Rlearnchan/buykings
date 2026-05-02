$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ProfileDir = Join-Path $RepoRoot "runtime\wepoll-fetcher-profile"
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$NodePath = "C:\Program Files\nodejs\node.exe"

Set-Location $RepoRoot

if (-not (Test-Path $ChromePath)) {
    throw "Chrome not found: $ChromePath"
}

if (-not (Test-Path $NodePath)) {
    throw "Node.js not found: $NodePath"
}

$NodeArgs = @(
    "scripts\wepoll_fetcher_daemon.mjs",
    "--user-data-dir",
    $ProfileDir,
    "--browser-path",
    $ChromePath,
    "--headed",
    "--allow-manual-login",
    "--verbose"
)

& $NodePath @NodeArgs
