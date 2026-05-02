param(
    [string]$Date = "",
    [switch]$SkipChromeLaunch,
    [switch]$SkipFedProbabilities,
    [switch]$SkipPublish,
    [switch]$SkipStateMirror
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$EnvPath = Join-Path $RepoRoot ".env"

function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Get-Content $Path | ForEach-Object {
        $Line = $_.Trim()
        if (-not $Line -or $Line.StartsWith("#") -or -not $Line.Contains("=")) { return }
        $Parts = $Line.Split("=", 2)
        $Name = $Parts[0].Trim()
        $Value = $Parts[1].Trim().Trim('"').Trim("'")
        if (-not [Environment]::GetEnvironmentVariable($Name, "Process")) {
            [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
        }
    }
}

Set-Location $RepoRoot
Import-DotEnv $EnvPath

if (-not (Test-Path $PythonExe)) {
    throw "Python venv executable not found: $PythonExe"
}

if (-not $env:AUTOPARK_CDP_ENDPOINT) {
    $env:AUTOPARK_CDP_ENDPOINT = "http://127.0.0.1:9222"
}
if (-not $env:AUTOPARK_PUBLISH_POLICY) {
    $env:AUTOPARK_PUBLISH_POLICY = "gate"
}
if (-not $env:AUTOPARK_STATE_ROOT) {
    $env:AUTOPARK_STATE_ROOT = Join-Path $RepoRoot ".server-state\autopark"
}

$Args = @("projects\autopark\scripts\run_live_dashboard_all_in_one.py")
if ($Date) { $Args += @("--date", $Date) }
if ($SkipChromeLaunch) { $Args += "--skip-chrome-launch" }
if ($SkipFedProbabilities) { $Args += "--skip-fed-probabilities" }
if ($SkipPublish) { $Args += "--skip-publish" }
if ($SkipStateMirror) { $Args += "--skip-state-mirror" }

& $PythonExe @Args
exit $LASTEXITCODE
