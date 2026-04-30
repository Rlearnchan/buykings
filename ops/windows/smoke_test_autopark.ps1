param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
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

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Body
    )
    Write-Host "== $Name =="
    & $Body
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Name"
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

Invoke-Step "runner dry-run" {
    & $PythonExe "projects\autopark\scripts\run_live_dashboard_all_in_one.py" --date $Date --dry-run
}

Invoke-Step "chrome cdp health" {
    Invoke-RestMethod -Uri "$($env:AUTOPARK_CDP_ENDPOINT.TrimEnd('/'))/json/version" -TimeoutSec 5 | ConvertTo-Json -Depth 4
}

Invoke-Step "x wallstengine dry-run" {
    node "projects\autopark\scripts\collect_x_timeline.mjs" --date $Date --run-name "smoke-x" --source "x-wallstengine" --cdp-endpoint $env:AUTOPARK_CDP_ENDPOINT --max-posts 2 --lookback-hours 48 --scrolls 1 --no-download-images --dry-run
}

Invoke-Step "finviz heatmap capture" {
    $BrowserArgs = @()
    if (-not $env:AUTOPARK_CHROME_PATH) { $BrowserArgs = @("--browser-channel", "chrome") }
    node "projects\autopark\scripts\capture_source.mjs" --date $Date --source "finviz-sp500-heatmap" --use-auth-profiles --headed @BrowserArgs --timeout-ms 45000 --no-full-page
}

Invoke-Step "datawrapper market dry-run" {
    & $PythonExe "projects\autopark\scripts\fetch_market_chart_data.py" --date $Date --chart "us10y" --collected-at (Get-Date -Format "yy.MM.dd HH:mm")
    & $PythonExe "scripts\datawrapper_publish.py" --dry-run "projects\autopark\charts\us10y-datawrapper.json"
}

Invoke-Step "notion publish dry-run" {
    & $PythonExe "projects\autopark\scripts\build_live_notion_dashboard.py" --date $Date
    $DateValue = [datetime]::ParseExact($Date, "yyyy-MM-dd", [Globalization.CultureInfo]::InvariantCulture)
    $Title = $DateValue.ToString("yy.MM.dd")
    & $PythonExe "projects\autopark\scripts\publish_recon_to_notion.py" --dry-run "projects\autopark\runtime\notion\$Date\$Title.md"
}

Write-Host "Autopark smoke test completed."
