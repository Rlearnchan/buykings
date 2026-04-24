param(
    [string]$TaskName = "BuyKingsMorning",
    [string]$StartTime = "11:35"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RunnerScript = Join-Path $RepoRoot "ops\windows\run_buykings_morning.ps1"
$PowerShellExe = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"

if (-not (Test-Path $RunnerScript)) {
    throw "Morning runner script not found: $RunnerScript"
}

if (-not (Test-Path $PowerShellExe)) {
    throw "PowerShell executable not found: $PowerShellExe"
}

$scheduledStart = [datetime]::Today.Add([timespan]::Parse($StartTime))
if ($scheduledStart -lt [datetime]::Now) {
    $scheduledStart = $scheduledStart.AddDays(1)
}

$action = New-ScheduledTaskAction `
    -Execute $PowerShellExe `
    -Argument "-ExecutionPolicy Bypass -File `"$RunnerScript`"" `
    -WorkingDirectory $RepoRoot

$trigger = New-ScheduledTaskTrigger -Daily -At $scheduledStart
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10)

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force | Out-Null

Get-ScheduledTask -TaskName $TaskName |
    Get-ScheduledTaskInfo |
    Select-Object LastRunTime, NextRunTime
