@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONPATH=%CD%
py -3 -m unittest discover -s studio/tests -v
if errorlevel 1 exit /b 1
py -3 -m unittest discover -s tests -v
exit /b %errorlevel%
