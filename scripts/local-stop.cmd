@echo off
REM Stops the local dev processes (Django :8000 and Next.js :3000).
taskkill /FI "WINDOWTITLE eq Compendium API*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Compendium Web*" /T /F 2>nul
echo Local development servers stopped.