$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot

Start-Process powershell -ArgumentList @(
  '-NoExit',
  '-ExecutionPolicy', 'Bypass',
  '-File', (Join-Path $PSScriptRoot 'start_test_portal_backend.ps1')
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
  '-NoExit',
  '-ExecutionPolicy', 'Bypass',
  '-File', (Join-Path $PSScriptRoot 'start_test_portal_frontend.ps1')
)

Write-Host 'Nexus test portal is starting locally: backend http://127.0.0.1:8001, frontend http://127.0.0.1:3001'
