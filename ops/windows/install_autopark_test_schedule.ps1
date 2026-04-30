param(
    [int]$IntervalMinutes = 30,
    [int]$DurationHours = 12,
    [string]$TaskName = "Autopark Test Cycle",
    [switch]$EnablePublish,
    [switch]$Unregister
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
$ChromeScript = Join-Path $PSScriptRoot "start_autopark_chrome.ps1"
$ChromeTaskName = "$TaskName Chrome"

if ($Unregister) {
    foreach ($Name in @($TaskName, $ChromeTaskName)) {
        $Existing = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
        if ($Existing) {
            Unregister-ScheduledTask -TaskName $Name -Confirm:$false
            Write-Host "Unregistered scheduled task: $Name"
        }
    }
    return
}

if (-not (Test-Path $CycleScript)) {
    throw "Autopark test cycle script not found: $CycleScript"
}
if (-not (Test-Path $ChromeScript)) {
    throw "Autopark Chrome script not found: $ChromeScript"
}

$StartAt = (Get-Date).AddMinutes(1)
$RepetitionInterval = New-TimeSpan -Minutes $IntervalMinutes
$RepetitionDuration = New-TimeSpan -Hours $DurationHours
$Trigger = New-ScheduledTaskTrigger -Once -At $StartAt -RepetitionInterval $RepetitionInterval -RepetitionDuration $RepetitionDuration

$CycleArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$CycleScript`"", "-SkipChromeLaunch")
if ($EnablePublish) {
    $CycleArgs += "-EnablePublish"
}
$CycleAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($CycleArgs -join " ") -WorkingDirectory $RepoRoot
$ChromeAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ChromeScript`"" -WorkingDirectory $RepoRoot
$ChromeTrigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $ChromeTaskName -Action $ChromeAction -Trigger $ChromeTrigger -Settings $Settings -Principal $Principal -Force | Out-Null
Register-ScheduledTask -TaskName $TaskName -Action $CycleAction -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName"
Write-Host "  interval: every $IntervalMinutes minutes"
Write-Host "  duration: $DurationHours hours from $($StartAt.ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host "  publish: $($EnablePublish.IsPresent)"
Write-Host "Registered Chrome profile task: $ChromeTaskName at logon"
Write-Host ""
Write-Host "Run once now:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\ops\windows\run_autopark_test_cycle.ps1"
Write-Host ""
Write-Host "Remove test tasks:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\ops\windows\install_autopark_test_schedule.ps1 -Unregister"
