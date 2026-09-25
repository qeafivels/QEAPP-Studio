@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "STUDIO=%QEAPP_STUDIO_HOME%"
if not defined STUDIO if exist "%~dp0..\..\run_studio.bat" set "STUDIO=%~dp0..\.."
if not defined STUDIO set /p "STUDIO=Nhap thu muc QEAPP-Studio v0.7.4: "
if not exist "%STUDIO%\run_studio.bat" (
 echo [ERROR] Khong tim thay run_studio.bat
 popd
 exit /b 2
)
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% "%STUDIO%\tools\qstudio.py" validate "%CD%\projects\pocket-calculator-lua"
if errorlevel 1 (
 echo [ERROR] Du an khong hop le.
 pause
 popd
 exit /b 3
)
echo [OK] Du an da duoc kiem tra.
echo Mo du an: %CD%\projects\pocket-calculator-lua
echo F9 = Virtual Phone Lua, F6 = Validate
call "%STUDIO%\run_studio.bat"
set "CODE=%ERRORLEVEL%"
popd
exit /b %CODE%
