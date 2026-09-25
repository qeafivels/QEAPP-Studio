@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul
if errorlevel 1 (
  set PY=python
) else (
  set PY=py -3
)
if exist "firmware\VQEAF-OS\lib\VqeafLua54\src\lua.h" (
  %PY% tools\verify_v041.py
) else (
  echo [INFO] Official Lua source missing: need tools\bootstrap_lua.py for real builds.
  echo [INFO] On Windows, system-lua fallback is NOT supported.
  exit /b 2
)
endlocal
