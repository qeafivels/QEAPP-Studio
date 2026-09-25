@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 tools\qstudio.py simulate --demo snake --scenario playing --frames 40 -o screenshots\snake.png
) else (
  python tools\qstudio.py simulate --demo snake --scenario playing --frames 40 -o screenshots\snake.png
)
if errorlevel 1 (
  echo [ERROR] C++17 compiler missing or build failed. Install g++ / clang++ and check PATH.
  exit /b 1
)
echo [OK] Screenshot saved at screenshots\snake.png (HOST ONLY).
