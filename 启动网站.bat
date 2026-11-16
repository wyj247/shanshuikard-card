@echo off
chcp 65001 >nul
setlocal
set PORT=%~1
if "%PORT%"=="" set PORT=8000
set PY=C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
if not exist "%PY%" set PY=python
"%PY%" "%~dp0site.py" %PORT%
pause