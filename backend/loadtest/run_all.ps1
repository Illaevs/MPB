# Load-test orchestrator. Starts an isolated load-test server (port 8002,
# raised rate limits, own DB copy) and runs Locust profiles headless.
# Reproduces the run; analysis is done from results/*_stats.csv + server.log.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$py   = Join-Path $repo '.venvs\test_portal\Scripts\python.exe'
$tp   = Join-Path $repo 'test_portal'
$res  = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Force -Path $res | Out-Null

$env:APP_VARIANT = 'test_portal'
$env:SECRET_KEY  = 'testportal-nexus-secret-key-should-be-long-and-isolated-2026-local-only-0123456789'
$env:SQLALCHEMY_DATABASE_URI = "sqlite:///$((Join-Path $tp 'crm_loadtest.db').Replace('\','/'))"
$env:STORAGE_BACKEND='local'
$env:STORAGE_LOCAL_ROOT=(Join-Path $tp 'storage')
$env:STATIC_LOCAL_ROOT=(Join-Path $tp 'static')
$env:UPLOAD_TMP_DIR=(Join-Path $tp 'tmp_uploads')
$env:AUTH_COOKIE_SECURE='false'
$env:REQUIRE_TWO_FACTOR='false'
$env:APP_HOST='127.0.0.1'; $env:APP_PORT='8002'; $env:APP_RELOAD='false'; $env:REDIS_URL=''
$env:API_RATE_LIMIT_READ_REQUESTS='2000000'
$env:API_RATE_LIMIT_WRITE_REQUESTS='2000000'

Set-Location $repo
$srv = Start-Process -FilePath $py -ArgumentList (Join-Path $repo 'backend\run.py') `
  -RedirectStandardOutput (Join-Path $res 'server.log') `
  -RedirectStandardError  (Join-Path $res 'server.err.log') `
  -PassThru -NoNewWindow
Start-Sleep -Seconds 6

function Run($name,$cls,$u,$r,$t,$extra=''){
  & $py -m locust -f (Join-Path $PSScriptRoot 'locustfile.py') --headless `
    -u $u -r $r -t $t --host http://127.0.0.1:8002 `
    --csv (Join-Path $res $name) --only-summary $cls
}

Run 'smoke'    'MixedUser' 1   1  60s
Run 'read'     'ReadUser'  100 10 120s
Run 'write'    'WriteUser' 40  8  90s
Run 'heavy'    'HeavyUser' 16  4  90s
Run 'soak'     'MixedUser' 40  8  300s

# Rate-limit verification: hit the default-limit server on :8001, no IP spoof.
$env:LOAD_SPOOF_IP='0'
& $py -m locust -f (Join-Path $PSScriptRoot 'locustfile.py') --headless `
  -u 60 -r 30 -t 30s --host http://127.0.0.1:8001 `
  --csv (Join-Path $res 'ratelimit') --only-summary ReadUser

Stop-Process -Id $srv.Id -Force
Write-Output 'DONE'
