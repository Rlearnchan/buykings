$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

Set-Location $RepoRoot

if (-not (Test-Path $PythonExe)) {
    throw "Python venv executable not found: $PythonExe"
}

& $PythonExe "scripts/run_buykings_morning.py"
