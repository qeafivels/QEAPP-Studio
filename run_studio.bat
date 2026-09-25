@echo off
setlocal EnableExtensions DisableDelayedExpansion
REM QEAPP Studio v0.7.4: stage safe dependency updates; test Qt window then activate.
REM Every launch checks local versions + pip consistency, installs missing libs,
REM checks updates every 24 h; failed staging preserves the previous environment.
REM Run with --offline to skip network; --update-now forces compatible upgrades.
REM Never construct a quoted executable plus -c in a single SET variable.
pushd "%~dp0" || (
    echo [ERROR] Cannot access QEAPP Studio directory.
    exit /b 2
)
set "PYTHONUTF8=1"
set "PYTHONDONTWRITEBYTECODE=1"
set "QEAPP_BOOT_PY="

REM Use base Python to inspect .venv; a broken venv must never prevent diagnosis.
where py.exe >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys,struct; sys.exit(0 if sys.version_info >= (3, 10) and struct.calcsize('P') * 8 == 64 else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "QEAPP_BOOT_PY=py"
        goto :launch_py
    )
)
where python.exe >nul 2>nul
if not errorlevel 1 (
    python -c "import sys,struct; sys.exit(0 if sys.version_info >= (3, 10) and struct.calcsize('P') * 8 == 64 else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "QEAPP_BOOT_PY=python"
        goto :launch
    )
)
if exist ".venv\Scripts\python.exe" (
    set "QEAPP_BOOT_PY=.venv\Scripts\python.exe"
    goto :launch
)
echo [ERROR] Python 3.10+ not found. Install 64-bit Python and enable the Python launcher.
echo         https://www.python.org/downloads/windows/
echo         After installation, reopen a terminal and run this file again.
goto :missing_python

:launch_py
echo [INFO] Checking safe updates and actual Qt GUI rendering before launching...
py -3 -B tools\studio_launcher.py %*
set "QEAPP_EXIT=%ERRORLEVEL%"
goto :finish

:launch
echo [INFO] Checking safe updates and actual Qt GUI rendering before launching...
"%QEAPP_BOOT_PY%" -B tools\studio_launcher.py %*
set "QEAPP_EXIT=%ERRORLEVEL%"
goto :finish

:missing_python
set "QEAPP_EXIT=2"
:finish
if not "%QEAPP_EXIT%"=="0" (
    echo.
    echo [ERROR] QEAPP Studio launcher exited with code %QEAPP_EXIT%.
    echo         Details: logs\launcher.log
    echo         Options: --diagnose, --repair, --gui-check, --rollback-update, --offline, --update-now
    if not defined QEAPP_NO_PAUSE pause
)
popd
endlocal & exit /b %QEAPP_EXIT%
