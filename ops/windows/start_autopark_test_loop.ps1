param(
    [int]$IntervalMinutes = 30,
    [int]$DurationHours = 12,
    [switch]$EnablePublish,
    [switch]$SkipChromeLaunch
)

$ErrorActionPreference = "Stop"

if ($IntervalMinutes -lt 5) {
    throw "IntervalMinutes must be at least 5."
}
if ($DurationHours -lt 1) {
    throw "DurationHours must be at least 1."
}

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$CycleScript = Join-Path $PSScriptRoot "run_autopark_test_cycle.ps1"
$EndAt = (Get-Date).AddHours($DurationHours)

Set-Location $RepoRoot

Write-Host "Autopark test loop started."
Write-Host "  interval: every $IntervalMinutes minutes"
Write-Host "  until: $($EndAt.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  publish: $($EnablePublish.IsPresent)"
Write-Host "Press Ctrl+C to stop."

while ((Get-Date) -lt $EndAt) {
    $StartedAt = Get-Date
    $Args = @("-ExecutionPolicy", "Bypass", "-File", $CycleScript)
    if ($EnablePublish) { $Args += "-EnablePublish" }
    if ($SkipChromeLaunch) { $Args += "-SkipChromeLaunch" }

    Write-Host ""
    Write-Host "[$($StartedAt.ToString('yyyy-MM-dd HH:mm:ss'))] Running Autopark test cycle..."
    & powershell.exe @Args
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        Write-Warning "Autopark test cycle exited with code $ExitCode"
    }

    $NextAt = $StartedAt.AddMinutes($IntervalMinutes)
    $SleepSeconds = [int][Math]::Max(0, ($NextAt - (Get-Date)).TotalSeconds)
    if ($SleepSeconds -gt 0 -and (Get-Date) -lt $EndAt) {
        Write-Host "Next run at $($NextAt.ToString('yyyy-MM-dd HH:mm:ss'))"
        Start-Sleep -Seconds $SleepSeconds
    }
}

Write-Host "Autopark test loop finished."
