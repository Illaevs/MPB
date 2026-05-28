$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venvs\test_portal\Scripts\python.exe'
$fallbackPythonExe = 'C:\Program Files\PostgreSQL\17\pgAdmin 4\python\python.exe'
$legacySitePackages = Join-Path $repoRoot '.venvs\test_portal\Lib\site-packages'
$testRoot = Join-Path $repoRoot 'test_portal'

if (-not (Test-Path $pythonExe) -or -not (Test-Path (Join-Path $testRoot 'crm_test_portal.db'))) {
  & (Join-Path $PSScriptRoot 'bootstrap_test_portal.ps1')
}

$env:APP_VARIANT = 'test_portal'
$env:SECRET_KEY = 'testportal-nexus-secret-key-should-be-long-and-isolated-2026-local-only-0123456789'
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///$((Join-Path $testRoot 'crm_test_portal.db').Replace('\','/'))"
$env:STORAGE_BACKEND = 'local'
$env:STORAGE_LOCAL_ROOT = (Join-Path $testRoot 'storage')
$env:STATIC_LOCAL_ROOT = (Join-Path $testRoot 'static')
$env:UPLOAD_TMP_DIR = (Join-Path $testRoot 'tmp_uploads')
$env:AUTH_COOKIE_SECURE = 'false'
$env:TWO_FACTOR_ISSUER = 'Nexus'
$env:REQUIRE_TWO_FACTOR = 'false'
$env:APP_HOST = '127.0.0.1'
$env:APP_PORT = '8001'
$env:APP_RELOAD = 'false'
$env:REDIS_URL = ''

Set-Location $repoRoot

$canUsePrimaryPython = $false
if (Test-Path $pythonExe) {
  try {
    & $pythonExe -c 'import uvicorn' *> $null
    if ($LASTEXITCODE -eq 0) {
      $canUsePrimaryPython = $true
    }
  } catch {
    $canUsePrimaryPython = $false
  }
}

if ($canUsePrimaryPython) {
  & $pythonExe (Join-Path $repoRoot 'backend\run.py')
  exit $LASTEXITCODE
}

if (-not (Test-Path $fallbackPythonExe)) {
  throw "Test portal Python is unavailable and fallback interpreter was not found: $fallbackPythonExe"
}

if (-not (Test-Path $legacySitePackages)) {
  throw "Legacy test portal site-packages not found: $legacySitePackages"
}

$backendEntry = (Join-Path $repoRoot 'backend\run.py')
$fallbackCode = @"
import runpy
import sys

sys.path.insert(0, r'$legacySitePackages')
runpy.run_path(r'$backendEntry', run_name='__main__')
"@

& $fallbackPythonExe -c $fallbackCode
exit $LASTEXITCODE
