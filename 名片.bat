@echo off
chcp 65001 >nul
setlocal
set "HERE=%~dp0"
set "PY=C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
set "NAME=%~1"
if "%NAME%"=="" set /p "NAME=Name: "
cd /d "%HERE%"
"%PY%" card.py "%NAME%" "%NAME%-card.png"
if errorlevel 1 (
  echo.
  echo Failed.
  pause
  exit /b 1
)
start "" "%NAME%-card.png"
endlocal
