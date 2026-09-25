@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where git >nul 2>&1 || exit /b 2
where gh >nul 2>&1 || exit /b 2
where py >nul 2>&1 || exit /b 2
py -3 tools\verify_separation.py --verify-remote || (echo [ERROR] New Studio repo not verified; keeping old OS branch intact.& exit /b 3)
set "TEMP_CLONE=%TEMP%\vqeaf_os_studio_cleanup_%RANDOM%"
if exist "%TEMP_CLONE%" (echo [ERROR] Temporary path conflict.& exit /b 4)
echo [INFO] Cloning ONLY old integration branch for cleanup...
git clone --single-branch --branch feat/qeapp-studio-samples-v074 https://github.com/qeafivels/VQEAF-OS.git "%TEMP_CLONE%" || exit /b 5
for /f "delims=" %%H in ('git -C "%TEMP_CLONE%" rev-parse HEAD') do set "OS_SHA=%%H"
if /I not "%OS_SHA%"=="68bd31e1cfb4e1b17d03679b0c3871f2a4b6ed7d" (
    echo [STOP] OS branch changed. Review its new content before removing Studio.
    echo [INFO] Preserved clone at %TEMP_CLONE%
    exit /b 6
)
if not exist "%TEMP_CLONE%\developer\QEAPP-Studio\AGENTS.md" (
    echo [STOP] The expected legacy Studio folder is missing.
    exit /b 6
)
git -C "%TEMP_CLONE%" rm -r -- developer/QEAPP-Studio || exit /b 7
if not exist "%TEMP_CLONE%\docs" mkdir "%TEMP_CLONE%\docs"
(
    echo # QEAPP-Studio now has an independent repository
    echo.
    echo The companion PC IDE and sample apps have moved to https://github.com/qeafivels/QEAPP-Studio
    echo VQEAF-OS is only firmware. No change to Retro-Go graphics or ESP32-S3 core.
    echo Set QEAPP_FIRMWARE_ROOT when using the IDE outside a sibling checkout.
)>"%TEMP_CLONE%\docs\QEAPP_STUDIO_RELOCATION.md"
git -C "%TEMP_CLONE%" add docs/QEAPP_STUDIO_RELOCATION.md || exit /b 7
git -C "%TEMP_CLONE%" commit -m "chore(os): relocate QEAPP Studio and samples to separate repository" || exit /b 7
git -C "%TEMP_CLONE%" push origin feat/qeapp-studio-samples-v074 || (
    echo [ERROR] Push failed; original OS branch unchanged. Clone kept at %TEMP_CLONE%
    exit /b 8
)
echo [OK] Old OS integration branch now contains only OS firmware and a Studio relocation link.
echo [INFO] OS main was never modified by this script.
exit /b 0
