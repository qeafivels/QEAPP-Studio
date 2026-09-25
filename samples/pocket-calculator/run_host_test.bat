@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "STUDIO=%QEAPP_STUDIO_HOME%"
if not defined STUDIO set /p "STUDIO=Nhap thu muc QEAPP-Studio v0.7.4: "
if not exist "%STUDIO%\tools\lua_preview.py" (
 echo [ERROR] Duong dan Studio sai.
 popd
 exit /b 2
)
where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
%PY% "%CD%\tests\verify_sample.py" --studio "%STUDIO%"
set "CODE=%ERRORLEVEL%"
popd
exit /b %CODE%
