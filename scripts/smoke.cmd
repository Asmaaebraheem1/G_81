@echo off
setlocal
cd /d "%~dp0.."

if not exist "backend\.venv\Scripts\python.exe" (
  echo Backend virtual environment not found.
  echo Create it with: py -3 -m venv backend\.venv ^&^& backend\.venv\Scripts\pip install -r backend\requirements-dev.txt
  exit /b 2
)

echo Running CarbonWise smoke test against http://127.0.0.1:5001/api/v1 ...
backend\.venv\Scripts\python.exe scripts\smoke.py --base http://127.0.0.1:5001/api/v1
exit /b %ERRORLEVEL%
