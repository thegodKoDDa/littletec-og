param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $projectRoot '.venv-qt-windows'
& $Python -m venv $environmentPath
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível criar o ambiente Python.' }
$environmentPython = Join-Path $environmentPath 'Scripts\python.exe'
& $environmentPython -m pip install -r (Join-Path $projectRoot 'requirements/windows-runtime.txt')
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar as dependências.' }
Write-Output "Preparado. Use: & '$environmentPython' '$projectRoot\tools\preview_qt.py'"
