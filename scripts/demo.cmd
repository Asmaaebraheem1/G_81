@echo off
setlocal
cd /d "%~dp0.."

set "BACKEND=%~dp0..\backend"
set "PY=%BACKEND%\.venv\Scripts\python.exe"
set "FLASK=%BACKEND%\.venv\Scripts\flask.exe"

if not exist "%PY%" (
  echo Backend virtual environment not found.
  echo Create it with: py -3 -m venv backend\.venv ^&^& backend\.venv\Scripts\pip install -r backend\requirements-dev.txt
  pause
  exit /b 2
)

if not exist "%BACKEND%\instance\carbonwise.sqlite3" (
  echo Seeding the demo database...
  pushd "%BACKEND%"
  "%FLASK%" --app app seed
  popd
)

echo Starting the CarbonWise backend on http://127.0.0.1:5001 ...
start "CarbonWise backend :5001" /D "%BACKEND%" cmd /k ".venv\Scripts\flask.exe --app app run --host 127.0.0.1 --port 5001"

timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:5001/admin/login"

echo.
echo Demo accounts:
echo   User:    sara@carbonwise.demo / User123!
echo   User:    ahmad@carbonwise.demo / User123!
echo   Org:     org@carbonwise.demo / Org123!
echo   Admin:   admin@carbonwise.demo / Admin123!
echo   Editor:  editor@carbonwise.demo / Editor123!
echo.
echo Mobile app (with an Android emulator already running):
echo   cd mobile
echo   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5001/api/v1
echo.
echo Admin panel: http://127.0.0.1:5001/admin/login
echo API docs:    http://127.0.0.1:5001/api
echo.
echo Close the backend window to stop the server.
endlocal
