@echo off
chcp 65001 >nul
setlocal
set "NAME=%~1"
if "%NAME%"=="" set /p "NAME=Name (2-4 chars, Chinese OK): "
if "%NAME%"=="" set "NAME=ShanShui"
set "PY=C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" "%~dp0shanshui.py" "%NAME%" "%~dp0%NAME%.png"
if errorlevel 1 (
  echo.
  echo Generation failed - see the message above.
  pause
  exit /b 1
)
start "" "%~dp0%NAME%.png"
