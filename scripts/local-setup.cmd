@echo off
REM ============================================================
REM Local development (no Docker) for the D&D Compendium.
REM
REM   scripts\local-setup.cmd     first time only
REM   scripts\local-start.cmd     start backend + frontend
REM   scripts\local-stop.cmd      stop frontend
REM ============================================================
setlocal
cd /d "%~dp0.."

set VENV=.venv
set PY=%VENV%\Scripts\python.exe

if not exist ".env" (
    echo.
    echo   No .env found. Creating from .env.example.local
    copy /y ".env.example.local" ".env" >nul
    echo   Done. Review .env if you changed your PostgreSQL password.
    echo.
)

where psql >nul 2>nul
if errorlevel 1 (
    echo   WARNING: psql not on PATH. PostgreSQL must be running on localhost:5432
    echo            with the credentials in .env before migrate will work.
    echo.
)

if not exist "%PY%" (
    echo   ERROR: virtualenv not found. Run: scripts\local-setup.cmd
    exit /b 1
)

echo == Applying migrations
pushd backend
"%PY%" manage.py migrate
popd

echo == Seeding category tree
pushd backend
"%PY%" manage.py seed_categories
popd

echo.
echo   Setup complete.
echo   Next: scripts\local-start.cmd
endlocal