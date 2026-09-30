@echo off
REM Full import of the 2024 compendium. Safe to re-run: already-imported
REM pages are skipped, so an interrupted run simply resumes.
setlocal
cd /d "%~dp0.."

set PY=.venv\Scripts\python.exe
set LOG=import_full.log

echo [%date% %time%] import started >> %LOG%
set PYTHONIOENCODING=utf-8
"%PY%" -m importer.cli import -y --delay 0.6 >> %LOG% 2>&1
echo [%date% %time%] import finished with exit code %ERRORLEVEL% >> %LOG%
echo DONE >> %LOG%
endlocal