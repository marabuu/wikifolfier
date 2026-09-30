@echo off
REM ============================================================
REM  Compendio D&D  -  stop backend and frontend
REM  Keeps ASCII-only, cmd breaks on accented chars.
REM ============================================================
setlocal
title Parar Compendio

echo  Encerrando os servicos...
echo.

taskkill /FI "WINDOWTITLE eq Compendium API*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq Compendium Web*" /T /F >nul 2>nul

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>nul

echo  Servicos encerrados.
echo.
endlocal