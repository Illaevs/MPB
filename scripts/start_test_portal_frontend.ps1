$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $repoRoot 'frontend')

$npmCmd = (Get-Command npm.cmd -ErrorAction Stop).Source
& $npmCmd 'run' 'dev:testportal' '--' '--host' '127.0.0.1' '--strictPort'
exit $LASTEXITCODE
