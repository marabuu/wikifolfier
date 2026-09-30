@echo off
REM Starts the Django API (:8000) and the Next.js frontend (:3000).
setlocal
cd /d "%~dp0.."

set PY=.venv\Scripts\python.exe

if not exist "%PY%" (
    echo ERROR: run scripts\local-setup.cmd first
    exit /b 1
)

echo == Starting Django on http://localhost:8000
start "Compendium API" cmd /k "cd /d "%CD%\backend" && "%CD%\%PY%" manage.py runserver 8000"

echo == Starting Next.js on http://localhost:3000
start "Compendium Web" cmd /k "cd /d "%CD%\frontend" && npm run dev"

echo.
echo   Frontend : http://localhost:3000
echo   API      : http://localhost:8000/api
echo   Health   : http://localhost:8000/api/health
echo   Admin    : http://localhost:8000/admin
echo.
echo   Close the two windows to stop.
endlocal