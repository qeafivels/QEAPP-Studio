@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [QEAPP Studio standalone migration]
where git >nul 2>&1 || (echo [ERROR] Please install Git for Windows.& exit /b 2)
where gh >nul 2>&1 || (echo [ERROR] Install GitHub CLI then rerun: https://cli.github.com/& exit /b 2)
where py >nul 2>&1 || (echo [ERROR] Install Python 3.10+ Windows launcher.& exit /b 2)
gh auth status || (echo [ERROR] Run "gh auth login" interactively in your terminal.& exit /b 2)
gh auth setup-git || (echo [ERROR] Git credential setup failed; refusing an unauthenticated push.& exit /b 2)
py -3 tools\verify_separation.py || (echo [ERROR] Source validation failed. Nothing pushed.& exit /b 3)
if not exist .git (
    git init -b main || exit /b 3
)
git branch --show-current | findstr /x main >nul || (echo [ERROR] Please use local main branch.& exit /b 3)
git add -A || exit /b 3
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "feat(studio): separate QEAPP Studio IDE and samples from VQEAF-OS" || (echo [ERROR] Configure git user.name/user.email and retry.& exit /b 3)
)
set "VISIBILITY=--public"
if /I "%~1"=="private" set "VISIBILITY=--private"
gh repo view qeafivels/QEAPP-Studio >nul 2>&1
if errorlevel 1 (
    echo [INFO] Creating QEAPP-Studio repository...
    gh repo create qeafivels/QEAPP-Studio %VISIBILITY% --source . --remote origin --push || exit /b 4
) else (
    git remote get-url origin >nul 2>&1 || git remote add origin https://github.com/qeafivels/QEAPP-Studio.git
    git push -u origin main || (echo [ERROR] Push rejected. New repo should be empty; no force push performed.& exit /b 4)
)
py -3 tools\verify_separation.py --verify-remote || (echo [ERROR] Remote validation failed. DO NOT clean OS branch.& exit /b 5)
echo [OK] Studio code and samples are on qeafivels/QEAPP-Studio main.
echo [NEXT] Run CLEAN_OS_FEATURE_BRANCH.bat only after this verification.
exit /b 0
