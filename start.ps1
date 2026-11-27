$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$forgePython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $forgePython)) {
    $forgePython = Join-Path $PSScriptRoot '../../work/coder-env/Scripts/python.exe'
}
if (-not (Test-Path -LiteralPath $forgePython)) {
    throw 'Run ./setup.ps1 first, then run ./start.ps1 again.'
}
& $forgePython server.py
