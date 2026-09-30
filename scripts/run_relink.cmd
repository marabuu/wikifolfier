@echo off
REM Re-import only subclass pages so structured_data stores their Wikidot path
REM (needed to link each subclass to its parent class), then backfill parents.
setlocal
cd /d "%~dp0.."
set PY=.venv\Scripts\python.exe
set PYTHONIOENCODING=utf-8

set LOG=relink.log
echo [%date% %time%] relink started >> %LOG%

"%PY%" -c "import sys; sys.path[:0]=[r'.',r'backend',r'importer']; from wikidot.filters import page_type_for; ps=[l.strip() for l in open('paths.txt',encoding='utf-8') if l.strip()]; subs=[p for p in ps if page_type_for(p)=='subclass']; open('subclass_paths.txt','w',encoding='utf-8').write('\n'.join(subs)); print('subclasses:',len(subs))" >> %LOG% 2>&1

"%PY%" -m importer.cli import -y --force --delay 0.5 --only-file subclass_paths.txt >> %LOG% 2>&1
"%PY%" scripts\link_parents.py >> %LOG% 2>&1

echo [%date% %time%] relink finished >> %LOG%
echo DONE >> %LOG%
endlocal