@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>&1 || exit /b 2
where git >nul 2>&1 || exit /b 2
where gh >nul 2>&1 || exit /b 2
py -3 tools\verify_separation.py --verify-remote || (echo [STOP] New Studio repo must be verified first.& exit /b 3)
set "TEMP_CLONE=%TEMP%\vqeaf_os_main_cleanup_%RANDOM%"
if exist "%TEMP_CLONE%" (echo [STOP] Temp folder conflict.& exit /b 4)
git clone --single-branch --branch main https://github.com/qeafivels/VQEAF-OS.git "%TEMP_CLONE%" || exit /b 5
for /f "delims=" %%H in ('git -C "%TEMP_CLONE%" rev-parse HEAD') do set "OS_MAIN_SHA=%%H"
if /I not "%OS_MAIN_SHA%"=="c1bb35c6d9767856b680ca75dcf7cefe0c24d04d" (
    echo [STOP] OS main has moved. Manually review before cleanup. Clone: %TEMP_CLONE%
    exit /b 6
)
if not exist "%TEMP_CLONE%\developer\QEAPP-Studio\GITHUB_STRUCTURE.md" (
    echo [STOP] Expected legacy scaffold file not found.
    exit /b 7
)
REM Main is expected to have only the old scaffold, never delete user-added files.
for /f %%C in ('git -C "%TEMP_CLONE%" ls-files developer/QEAPP-Studio ^| find /c /v ""') do set "FILE_COUNT=%%C"
if not "%FILE_COUNT%"=="1" (echo [STOP] Main contains additional Studio files; do not delete.& exit /b 7)
git -C "%TEMP_CLONE%" rm -- developer/QEAPP-Studio/GITHUB_STRUCTURE.md || exit /b 8
if not exist "%TEMP_CLONE%\docs" mkdir "%TEMP_CLONE%\docs"
(
    echo # QEAPP-Studio independent repository
    echo.
    echo The PC IDE and examples now live in https://github.com/qeafivels/QEAPP-Studio
    echo The OS repository remains the ESP32-S3 firmware and Retro-Go renderer.
    echo Set QEAPP_FIRMWARE_ROOT in Studio to this firmware checkout when signing packages.
)>"%TEMP_CLONE%\docs\QEAPP_STUDIO_RELOCATION.md"
git -C "%TEMP_CLONE%" add docs/QEAPP_STUDIO_RELOCATION.md || exit /b 8
git -C "%TEMP_CLONE%" commit -m "docs(os): point to standalone QEAPP Studio repository" || exit /b 8
git -C "%TEMP_CLONE%" push origin main || (
    echo [STOP] Push rejected: main moved or protected. Clone preserved: %TEMP_CLONE%
    exit /b 9
)
echo [OK] Main scaffold replaced with a link. Firmware code and graphics unchanged.
exit /b 0
