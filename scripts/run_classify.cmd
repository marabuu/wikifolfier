@echo off
REM Re-import spells and Unearthed Arcana pages so their structured data
REM carries spell classes and the wikidot path, then classify sub-categories.
setlocal
cd /d "%~dp0.."
set PY=.venv\Scripts\python.exe
set PYTHONIOENCODING=utf-8
set LOG=classify.log

echo [%date% %time%] started >> %LOG%

"%PY%" -c "import sys; sys.path[:0]=[r'.',r'backend',r'importer']; from wikidot.filters import page_type_for; ps=[l.strip() for l in open('paths.txt',encoding='utf-8') if l.strip()]; want=[p for p in ps if page_type_for(p)=='spell' or p.startswith('ua:')]; open('respell_paths.txt','w',encoding='utf-8').write('\n'.join(want)); print('targets:',len(want))" >> %LOG% 2>&1

"%PY%" -m importer.cli import -y --force --delay 0.5 --only-file respell_paths.txt >> %LOG% 2>&1

pushd backend
"%PY%" manage.py classify >> ..\%LOG% 2>&1
popd

echo [%date% %time%] finished >> %LOG%
echo DONE >> %LOG%
endlocal