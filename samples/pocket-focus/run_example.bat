@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "STUDIO=%QEAPP_STUDIO_HOME%"
if not defined STUDIO if exist "%~dp0..\..\run_studio.bat" set "STUDIO=%~dp0..\.."
if not defined STUDIO (
  echo QEAPP Studio root not configured.
  set /p "STUDIO=Full path to QEAPP-Studio v0.7.4: "
)
if not exist "%STUDIO%\run_studio.bat" (
 echo [ERROR] Cannot locate Studio run_studio.bat
 popd
 exit /b 2
)
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% "%STUDIO%\tools\qstudio.py" validate "%CD%\projects\pocket-focus-lua"
if errorlevel 1 (
 echo [ERROR] Project validation failed.
 pause
 popd
 exit /b 3
)
echo [OK] Sample valid. Choose File / Open Project and select:
echo      %CD%\projects\pocket-focus-lua
echo Press F9 to launch virtual phone.
call "%STUDIO%\run_studio.bat"
set "STATUS=%ERRORLEVEL%"
popd
exit /b %STATUS%
