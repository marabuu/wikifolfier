@echo off
setlocal
cd /d "%~dp0"

title Compendio D&D - iniciar

echo.
echo ============================================
echo   Iniciando backend e frontend
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo Rode scripts\local-setup.cmd uma vez antes de iniciar.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERRO] Dependencias do frontend nao encontradas.
    echo Rode: cd frontend ^&^& npm install
    pause
    exit /b 1
)

echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.

if exist "frontend\.next" rmdir /s /q "frontend\.next"

start "Compendium API" /D "%CD%\backend" cmd /k ""%CD%\.venv\Scripts\python.exe" manage.py runserver 8000"
timeout /t 2 /nobreak >nul
start "Compendium Web" /D "%CD%\frontend" cmd /k "npm.cmd run dev"

timeout /t 5 /nobreak >nul
start "" http://localhost:3000

echo Duas janelas foram abertas.
echo Para encerrar, execute parar.bat.
echo.
endlocal
