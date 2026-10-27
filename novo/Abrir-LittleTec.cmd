@echo off
pushd "%~dp0" >nul 2>&1
set "APP_DIR=%LOCALAPPDATA%\LittleTec\App"
robocopy "%CD%\dist" "%APP_DIR%" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
start "" "%APP_DIR%\LittleTec.exe"
popd >nul 2>&1
