$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venvs\test_portal\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
  python -m venv (Join-Path $repoRoot '.venvs\test_portal')
  & $pythonExe -m pip install --upgrade pip
  & $pythonExe -m pip install -r (Join-Path $repoRoot 'backend\requirements.txt')
}

& $pythonExe (Join-Path $repoRoot 'backend\scripts\bootstrap_test_portal.py')
