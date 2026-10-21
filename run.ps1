param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$cvboostPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $cvboostPython)) {
    throw 'Create .venv and install requirements.txt first. See README.md.'
}
& $cvboostPython -m uvicorn main:app --host 127.0.0.1 --port $Port
