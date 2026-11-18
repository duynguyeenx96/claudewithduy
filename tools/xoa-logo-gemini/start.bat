@echo off
rem Windows: bam dup de chay.
cd /d "%~dp0"
if "%PORT%"=="" set PORT=8768
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
if not exist node_modules\@pilio (
  call npm install --ignore-scripts || (echo npm install loi & pause & exit /b 1)
)
start "" "http://localhost:%PORT%"
%PY% server.py
pause
