@echo off
REM ============================================================
REM  Compendio DandeD - start backend (Django) and frontend
REM  Frontend : http://localhost:3000
REM  API      : http://localhost:8000/api
REM  Stop with parar.bat
REM  NOTE: ASCII-only, no nested parentheses blocks. cmd is fragile.
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  ============================================
echo   Compendio DandeD - iniciando
echo  ============================================
echo.

if exist ".env" goto env_ok
if not exist ".env.example.local" goto env_error
echo  [1/4] Criando .env a partir do modelo...
copy /y ".env.example.local" ".env" >nul
echo         .env criado.
goto env_ok

:env_error
echo  [ERRO] .env nao encontrado e sem modelo para copiar.
goto fail

:env_ok
if not exist ".venv\Scripts\python.exe" goto no_venv
echo  [1/4] .env e ambiente virtual OK.

if exist "frontend\node_modules" goto deps_ok
echo  [3/4] Instalando dependencias do frontend (pode demorar)...
pushd frontend
call npm install
popd

:deps_ok
echo.
echo  [4/4] Iniciando os servicos...
echo.
echo        Frontend : http://localhost:3000
echo        API      : http://localhost:8000/api
echo        Health   : http://localhost:8000/api/health
echo.

start "Compendium API" /D "%CD%\backend" cmd /k "..\.venv\Scripts\python.exe manage.py runserver 8000"
timeout /t 2 /nobreak >nul
start "Compendium Web" /D "%CD%\frontend" cmd /k "npm run dev"

echo  Duas janelas foram abertas. Feche-as para parar.
echo.
timeout /t 10 /nobreak >nul
start "" http://localhost:3000
endlocal

:no_venv
echo.
echo  [ERRO] Ambiente virtual nao encontrado.
echo         Rode scripts\local-setup.cmd
goto fail

:fail
echo.
pause
endlocal