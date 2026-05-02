param(
    [string]$StartAt,
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$SkipChromeLaunch,
    [switch]$SkipPublish,
    [switch]$SkipStateMirror
)

$ErrorActionPreference = "Stop"

if (-not $StartAt) {
    throw "StartAt is required. Example: -StartAt 23:50"
}

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RunScript = Join-Path $PSScriptRoot "run_autopark_daily.ps1"

Set-Location $RepoRoot

$Today = Get-Date -Format "yyyy-MM-dd"
$Target = [datetime]::ParseExact("$Today $StartAt", "yyyy-MM-dd HH:mm", $null)
if ($Target -le (Get-Date)) {
    $Target = $Target.AddDays(1)
}

$SleepSeconds = [int][Math]::Max(0, ($Target - (Get-Date)).TotalSeconds)
Write-Host "Autopark one-shot scheduled."
Write-Host "  target: $($Target.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  date: $Date"
Write-Host "  publish: $(-not $SkipPublish.IsPresent)"
Write-Host "  skip chrome launch: $($SkipChromeLaunch.IsPresent)"

if ($SleepSeconds -gt 0) {
    Start-Sleep -Seconds $SleepSeconds
}

$Args = @("-ExecutionPolicy", "Bypass", "-File", $RunScript, "-Date", $Date)
if ($SkipChromeLaunch) { $Args += "-SkipChromeLaunch" }
if ($SkipPublish) { $Args += "-SkipPublish" }
if ($SkipStateMirror) { $Args += "-SkipStateMirror" }

Write-Host "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))] Running Autopark..."
& powershell.exe @Args
exit $LASTEXITCODE
