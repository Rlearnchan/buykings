param(
    [int]$Port = 9222,
    [string]$RemoteAddress = "127.0.0.1",
    [string]$StartUrl = "https://x.com/wallstengine"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
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

function Resolve-ChromePath {
    if ($env:AUTOPARK_CHROME_PATH -and (Test-Path $env:AUTOPARK_CHROME_PATH)) {
        return $env:AUTOPARK_CHROME_PATH
    }
    $Candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
    )
    foreach ($Candidate in $Candidates) {
        if ($Candidate -and (Test-Path $Candidate)) { return $Candidate }
    }
    return "chrome.exe"
}

Import-DotEnv $EnvPath

if (-not $env:AUTOPARK_CDP_ENDPOINT) {
    $env:AUTOPARK_CDP_ENDPOINT = "http://127.0.0.1:$Port"
}

$StateRoot = $env:AUTOPARK_STATE_ROOT
if (-not $StateRoot) {
    $StateRoot = Join-Path $RepoRoot ".server-state\autopark"
}

$ProfileDir = $env:AUTOPARK_CDP_PROFILE
if (-not $ProfileDir) {
    $ProfileDir = Join-Path $StateRoot "profiles\chrome-cdp"
}
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$ChromePath = Resolve-ChromePath
$Urls = @(
    $StartUrl,
    "https://finviz.com/",
    "https://x.com/eWhispers",
    "https://www.cmegroup.com/ko/markets/interest-rates/cme-fedwatch-tool.html",
    "https://polymarket.com/markets?search=fed%20rate%20cut"
)

$Arguments = @(
    "--remote-debugging-address=$RemoteAddress",
    "--remote-debugging-port=$Port",
    "--user-data-dir=$ProfileDir",
    "--profile-directory=Default",
    "--start-maximized",
    "--window-size=1920,1080",
    "--force-device-scale-factor=1"
) + $Urls

Start-Process -FilePath $ChromePath -ArgumentList $Arguments -WorkingDirectory $RepoRoot
Start-Sleep -Seconds 4

$Health = $null
$DockerHealth = $null
try {
    $Health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 5
} catch {
    Write-Warning "Chrome CDP did not respond yet: $($_.Exception.Message)"
}
try {
    $DockerHealth = Invoke-RestMethod -Uri "http://host.docker.internal:$Port/json/version" -TimeoutSec 5
} catch {
    Write-Warning "Chrome CDP did not respond via host.docker.internal yet: $($_.Exception.Message)"
}

[pscustomobject]@{
    ok = [bool]$Health
    docker_ok = [bool]$DockerHealth
    endpoint = "http://127.0.0.1:$Port"
    docker_endpoint = "http://host.docker.internal:$Port"
    remote_address = $RemoteAddress
    chrome_path = $ChromePath
    profile_dir = $ProfileDir
    login_note = "Keep this Chrome profile logged in for X, Finviz, Earnings Whispers, FedWatch, and Polymarket."
} | ConvertTo-Json -Depth 4
