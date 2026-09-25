# QEAPP Studio v0.7.1 — Windows launcher / environment preflight

Start by double-clicking `run_studio.bat` from an extracted **full source** folder.
The wrapper runs the standard-library-only `tools/studio_launcher.py`. It does not
use the fragile `set PY=...` / `"%PY%"` command concatenation pattern.

## First run

1. Detect Python 3.10+ through `py -3` or `python.exe`; use a valid existing
   project `.venv` or create a fresh `.venv` automatically. The launcher checks
   its Python interpreter without deleting an existing virtual environment.
2. Inspect required package versions from `requirements-studio.txt`: PySide6,
   cryptography and Pillow. Run `pip install -r requirements-studio.txt` **only if
   missing/outdated**, scoped to the selected Python. Dependencies are not
   silently installed globally by default.
3. Execute an isolated Qt **offscreen** application creation smoke test, also
   importing `cryptography` and `Pillow`, before launching the real Qt window.
   This catches many DLL/package errors early without claiming Windows GUI
   verification on a machine where Windows was not available.
4. Check the Lua 5.4 upstream source directory, gcc/g++ and `build/qe_lua_host.exe`.
   If both source and toolchain exist, build the PC host VM only when absent or
   when core inputs changed. Missing optional VM dependencies are **warnings**:
   the source editor still opens, but live Lua Run/F9 requires the VM.
5. Start `run_studio.py` using the selected Python; diagnostic stderr is
   appended to `logs/gui-crash.log`. Launcher details are logged to
   `logs/launcher.log`. Old launcher logs are rotated above 1 MB.

## Options (in Command Prompt)

```bat
run_studio.bat                     REM Normal setup and GUI
run_studio.bat --check-only        REM Inspect existing .venv, no installs, no GUI
run_studio.bat --system            REM Use existing system Python / installed packages
run_studio.bat --no-install        REM Never run pip
run_studio.bat --repair            REM Back up corrupt settings/broken .venv; install missing libs
run_studio.bat --reinstall-deps    REM Explicit force reinstall project Python dependencies
run_studio.bat --diagnose         REM Read-only checks, does not launch GUI
run_studio.bat --setup-lua         REM Explicitly download verified Lua 5.4.8 source
run_studio.bat --build-vm          REM Force recompile Lua host if gcc/g++ are installed
run_studio.bat --require-vm        REM Fail preflight unless Lua host VM exists
```

To perform a read-only system Python check before the first launch:
`run_studio.bat --system --check-only` (will fail if required libraries have
not yet been installed in that interpreter).

**Optional full Lua VM setup:** install an appropriate Windows gcc/g++ toolchain
(e.g. MSYS2 MinGW-w64), confirm both are on PATH, and run
`run_studio.bat --setup-lua --build-vm`. `bootstrap_lua.py` verifies the
**official Lua archive SHA256** before installing the firmware/host sources.
There is no automatic third-party source download on a normal GUI launch.

## Troubleshooting

- `Python 3.10+ not found`: install 64-bit Python and reopen a terminal.
- `.venv appears broken`: rename `.venv` to a backup and rerun; projects are
  never erased by the launcher.
- `pip installation failed`: verify network/certificates/proxy and inspect
  `logs/launcher.log`; use `--system` if already installed outside `.venv`.
- `Qt failed to load`: use `--diagnose`, then optionally `--reinstall-deps`; check conflicting Qt environment variables
  and your Windows C++ runtime. The offscreen test is isolated and does not
  change your GUI environment variables.
- Missing VM compiler: install gcc and g++ for host builds; still use the
  project editor and non-Lua preview until the toolchain is configured.
- Qt GUI launches then exits unexpectedly: read `logs/gui-crash.log` and
  `logs/launcher.log` for the exit code and Python traceback.

Test coverage: `python -m unittest studio.tests.test_launcher_v071 -v` validates
pure-Python logic and checks batch script structure. An actual Windows CMD +
PySide6 interactive startup must still be run on a Windows developer PC.
No ESP32-S3 / ST7789 / SD / installer is emulated by this launcher.
