param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$EnablePublish,
    [switch]$SkipChromeLaunch,
    [switch]$SkipStateMirror
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RunScript = Join-Path $PSScriptRoot "run_autopark_daily.ps1"

if (-not (Test-Path $RunScript)) {
    throw "Autopark runner not found: $RunScript"
}

Set-Location $RepoRoot

$Args = @("-ExecutionPolicy", "Bypass", "-File", $RunScript, "-Date", $Date)
if ($SkipChromeLaunch) { $Args += "-SkipChromeLaunch" }
if ($SkipStateMirror) { $Args += "-SkipStateMirror" }
if (-not $EnablePublish) { $Args += "-SkipPublish" }

Write-Host "Autopark test cycle starting. Date=$Date Publish=$($EnablePublish.IsPresent)"
& powershell.exe @Args
exit $LASTEXITCODE
