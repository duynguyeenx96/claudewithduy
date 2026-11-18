@echo off
rem Windows: bam dup de chay.
cd /d "%~dp0"
if "%PORT%"=="" set PORT=8769
where py >nul 2>nul && (set PY=py -3) || (set PY=python)

start "" "http://localhost:%PORT%"
%PY% server.py
pause
