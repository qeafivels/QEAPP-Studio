# QEAPP Studio v0.7.2 — Lua host VM / IDE / GUI diagnostics / Safe Repair

## What's implemented

**Shared Lua runtime (`runtime/src/`, firmware beta mirror)**
- `engine.heap_used()` and `engine.heap_peak()` expose the same bounded Lua allocator counters as host diagnostics. They do **not** include all ESP32/PC process RAM.
- Host interactive CLI adds `--interactive --heap-kib 96|192|384`, default still 192 KiB; rejects unknown heap flags and unreasonable sizes. GUI exposes these three caps and restarts the host subprocess when requested.
- The host emits `QEHOST_METRIC` every 10 frames; all metrics are PC host readings, not ESP32.
- Existing instruction, time, draw, memory and script-size guards remain enabled. OS-reserved keys (MENU/Back) are not injected into guest Lua. B/Delete and T9 are visibly labelled unsupported rather than simulated incorrectly.

**IDE / virtual device (`studio/gui/`)**
- Uses the existing original dark blue/violet IDE layout: native system-icon activity rail; searchable file Explorer; multi-tab source editing; View / Run / Tools menu; Output / Problems panel and virtual-device tabs.
- Adds Diagnostics tab with live VM inspector, GUI/host environment checks and Safe Repair. F9 starts, Pause/Resume stops timer tick, Step renders one bounded VM frame, Ctrl+Shift+R restarts a fresh VM, and 15/30/60 FPS **timer caps** can be selected. Real FPS shown separately.
- Lua host errors containing verified `signed-qeapp-main.lua:<line>:` diagnostics create a Problems entry and navigate to the source line. Unknown errors still appear in Problems without inventing a location.

**Debugging (`studio/core/diagnostics.py`)**
- GUI `sys.excepthook` records unexpected Python GUI exceptions under local `logs/gui-errors.log`; launcher already records native startup stderr to `logs/gui-crash.log` and preflight status to `logs/launcher.log`.
- Optional `Debug session` captures bounded JSONL events (`start/stop/key/frame/step/pause/resume/watchdog`) with safe numeric counters only. Source, arbitrary paths, Lua error text, passwords and signing keys are not serialized. Logs are local, rotated when large; console output remains visible.
- VM stall watchdog still terminates hung guest processes; recovery is an explicit fresh restart, never silently reload a corrupt snapshot.

**Safe repair (`studio/core/repair.py`, `tools/studio_doctor.py`)**
- Read-only `--diagnose` checks Python dependencies, Lua source, toolchain, host VM and settings schema even when PySide6 is absent; does **not** create `.venv` or install anything.
- `run_studio.bat --repair` backs up corrupt user JSON settings and any broken `.venv` before replacing them, then performs normal dependency preflight. Never touches source projects, signing keys, embedded firmware or SD contents. No silent auto-flashing.
- `--reinstall-deps` is an **independent explicit opt-in** for pip force-reinstall; safe repair alone installs only missing/outdated packages as needed for ordinary GUI launch.
- GUI `Tools → Safe Repair Mode…` previews checks and requires confirmation. It only backs up/resets malformed **user settings.json**; broken `.venv` repair requires launcher `--repair` when Qt cannot open. `Tools → Reset IDE Layout` also requires confirmation and never modifies source.

## Commands on Windows

```bat
run_studio.bat --diagnose
run_studio.bat --repair
run_studio.bat --repair --reinstall-deps
run_studio.bat --setup-lua --build-vm
run_studio.bat
```

The launcher requires Python 3.10+ x64 and matching PySide6/Pillow/cryptography versions. `--diagnose` is **read-only**. With no system GCC/G++ for the host runner, the GUI still opens if Python/Qt dependencies are available; the Lua VM needs host tooling to run. Neither GUI preview nor Lua host test is proof of firmware behavior on physical ESP32-S3.

Linux *diagnostic-only* reproduction when system liblua5.4 is available:

```bash
python tools/verify_v072.py --system-lua
python tools/studio_doctor.py --json
```

For actual Windows GUI evidence, install dependencies then run:

```bat
run_studio.bat --check-only
py -3 tools/verify_v072.py --require-qt
run_studio.bat
```

For physical ESP32-S3 release, separately compile with PlatformIO, flash correct beta signing trust anchor, run `.qeapp` install/execute and collect 115200 baud serial, FPS/latency/heap/leak evidence. No part of v0.7.2's PC-host report claims those steps occurred.
