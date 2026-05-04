param(
    [string]$TaskName = "Autopark Daily Publish",
    [string]$ChromeTaskName = "Autopark Chrome CDP",
    [string]$RunAt = "05:30",
    [string]$ChromeAt = "05:20",
    [switch]$SkipPublish,
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RunScript = Join-Path $PSScriptRoot "run_autopark_daily.ps1"
$ChromeScript = Join-Path $PSScriptRoot "start_autopark_chrome.ps1"

function New-DailyTrigger {
    param([string]$TimeText)
    $today = Get-Date -Format "yyyy-MM-dd"
    $at = [datetime]::ParseExact("$today $TimeText", "yyyy-MM-dd HH:mm", $null)
    return New-ScheduledTaskTrigger -Daily -At $at
}

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

if (-not (Test-Path $RunScript)) {
    throw "Autopark daily script not found: $RunScript"
}
if (-not (Test-Path $ChromeScript)) {
    throw "Autopark Chrome script not found: $ChromeScript"
}

$CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$Principal = New-ScheduledTaskPrincipal -UserId $CurrentUser -LogonType Interactive -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -RestartCount 1 `
    -RestartInterval (New-TimeSpan -Minutes 5)

$ChromeAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ChromeScript`" -StartUrl https://finviz.com/" `
    -WorkingDirectory $RepoRoot
$ChromeTriggers = @()
$ChromeTriggers += New-ScheduledTaskTrigger -AtLogOn
$ChromeTriggers += New-DailyTrigger -TimeText $ChromeAt

$RunArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$RunScript`"")
if ($SkipPublish) {
    $RunArgs += "-SkipPublish"
}
$RunAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument ($RunArgs -join " ") `
    -WorkingDirectory $RepoRoot
$RunTrigger = New-DailyTrigger -TimeText $RunAt

try {
    Register-ScheduledTask -TaskName $ChromeTaskName -Action $ChromeAction -Trigger $ChromeTriggers -Settings $Settings -Principal $Principal -Force | Out-Null
    Register-ScheduledTask -TaskName $TaskName -Action $RunAction -Trigger $RunTrigger -Settings $Settings -Principal $Principal -Force | Out-Null
} catch {
    Write-Warning "Register-ScheduledTask failed; falling back to schtasks.exe daily tasks only: $($_.Exception.Message)"
    schtasks.exe /Create /TN $ChromeTaskName /SC DAILY /ST $ChromeAt /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ChromeScript" /F | Out-Host
    $TaskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RunScript"
    if ($SkipPublish) {
        $TaskCommand += " -SkipPublish"
    }
    schtasks.exe /Create /TN $TaskName /SC DAILY /ST $RunAt /TR $TaskCommand /F | Out-Host
}

Write-Host "Registered scheduled task: $ChromeTaskName"
Write-Host "  triggers: at logon; daily $ChromeAt"
Write-Host "  action: start visible Chrome CDP profile"
Write-Host "Registered scheduled task: $TaskName"
Write-Host "  trigger: daily $RunAt"
Write-Host "  publish: $(-not $SkipPublish.IsPresent)"
Write-Host "  runner: $RunScript"
