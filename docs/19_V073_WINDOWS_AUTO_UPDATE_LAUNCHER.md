# QEAPP Studio v0.7.3 — Windows startup auto-check / auto-update

Double-click `run_studio.bat` in the **fully extracted ZIP folder**. Do not run
this script from inside a ZIP archive. This package is based on the full v0.7.2
source and preserves the existing VM, IDE, renderer and QEAPP signing behavior.

## Normal launch, in order

1. Find a usable Python **3.10+ 64-bit**, prefer `py -3`, then `python`. An existing
   `.venv` is validated. If absent, an **isolated project** virtual environment
   is created. If an existing venv is broken, **explicit** `--repair` backs it up
   before creating a replacement; no project or signing key is deleted.
2. Check versions for PySide6, cryptography and Pillow on **every launch** and run
   `python -m pip check` to detect dependency conflicts. Install/fix missing or
   incompatible requirements in `.venv` automatically (requires network).
3. If local dependencies are healthy, automatically check for **compatible newer
   versions once per 24 hours** using `pip install --upgrade -r requirements-studio.txt`.
   The local cache is tied to Python interpreter path and requirements SHA-256.
   Failed online checks back off for 6 hours. If a failed update leaves all local
   libraries healthy, GUI launch can continue. No arbitrary forced package upgrade
   on every application start: this avoids repeatedly blocking the IDE.
4. Start a separate **Qt offscreen test** to verify PySide6 QApplication, Pillow
   and cryptography imports. This is a smoke test, NOT proof Windows interactive
   rendering has succeeded; real GUI launch is the final stage.
5. Check local Lua source, GCC/G++ and host VM. If all exist, rebuild outdated VM.
   The GUI still opens when optional host VM tooling is absent. **No automatic
   internet download of the Lua C source**; use `--setup-lua` explicitly.
6. Start `run_studio.py`, showing console progress and retaining logs:
   `logs/launcher.log`, `logs/gui-crash.log`, `logs/gui-errors.log` (unexpected Python errors).

## Commands

```bat
run_studio.bat                         REM Check, auto-install/periodic upgrade, GUI
run_studio.bat --update-now            REM Explicit compatible upgrade now, then GUI
run_studio.bat --no-update             REM Install missing but skip optional upgrades
run_studio.bat --offline               REM No network: require installed dependencies
run_studio.bat --check-only            REM Read-only local checks; no GUI or upgrades
run_studio.bat --diagnose              REM Read-only doctor (works even without Qt)
run_studio.bat --repair                REM Backup broken venv/settings then fix + GUI
run_studio.bat --repair --reinstall-deps REM Force fresh Python library reinstall
run_studio.bat --setup-lua --build-vm   REM Explicitly set up verified Lua host source
```

`--system` uses system Python at your **explicit** request. It does not silently
upgrade global packages periodically; use `--system --update-now` if you intend
that change. By default, package upgrades affect the local `.venv` only.
`--offline`, `--no-install`, `--check-only`, `--no-update` and `--update-now` are
validated against incompatible combinations. `--offline` never downloads Lua.

**Troubleshooting:** If Windows cannot load a Qt DLL, try
`run_studio.bat --diagnose`, inspect `logs/launcher.log`, then
`run_studio.bat --repair --reinstall-deps` only if needed. GUI errors are
reported in `logs/gui-crash.log`. A failed update due to offline network does not
mean a previously working GUI will be blocked if integrity and Qt checks pass.

**Security/scope:** Dependencies come from your configured pip package indexes;
for stronger reproducibility deploy an approved internal mirror or pinned wheel
bundle. Python package updates do not flash ESP32-S3, modify firmware, install
QEAPP games, overwrite PEM signing keys, or prove real TFT/SD/audio behavior.

**Validation:** `python -m unittest studio.tests.test_launcher_v073 -v` checks
update scheduling, failed-network fallback, read-only/offline behavior and
install repair in isolation without actually downloading packages. Full tests:
`python -m unittest discover -s studio/tests -v` (PySide6-only tests skip where Qt
is not installed). Execute `run_studio.bat` on an actual Windows desktop for
interactive GUI verification; PC/Linux tests alone cannot establish that status.
