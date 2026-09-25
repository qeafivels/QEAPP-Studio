# QEAPP Studio v0.6 — release verification

Source baseline: QEAPP Studio v0.5 previous release, with an independent M3
PySide6 layout and a persistent **real PC Lua 5.4 host VM** added on top.

## Observed checks

| Check | Result | Scope |
|---|---|---|
| Python static compilation | PASS | `window.py`, `virtual_phone.py`, binary parser |
| C++17 host Lua build | PASS | compiled using **system Lua 5.4**, Linux diagnostic only |
| Studio unit tests + stream/keyboard safety | 34 total, 31 PASS, 3 SKIPPED | Qt-dependent tests skipped because PySide6 unavailable |
| Real persistent host VM + PNG | PASS | 14 frames, 129,600 bytes RGB565 per guest frame |
| Legacy v0.5 gate | PASS **on prior intermediate v0.6 work tree** | original host runtime, signature/unit/firmware-mock/sprite smoke passed; latest full rerun timed out; must rerun before release to device |
| PySide6 visual runtime on this machine | NOT RUN | Qt could not be installed here (network DNS unavailable) |
| ESP32-S3 PlatformIO / real device | NOT RUN | no board/toolchain connected |
| QEAPP firmware install / app/theme simulation | NOT IN DESKTOP VM | firmware-only behavior; not claimed |

The UI screenshot `QEAPP_Studio_v06_UI_Concept.png` is a **manually rendered
illustrative layout**, NOT a Qt window capture. The game screen
`QEAPP_Studio_v06_Lua_Snake_Host_Frame.png` comes from **actual Lua VM output
through the new persistent binary frame protocol**. Neither image is an
ESP32-S3 screenshot.

## Reproducible commands

Install PySide6 on a Windows development host:

```powershell
py -3 -m pip install -r requirements-studio.txt
py -3 tools/bootstrap_lua.py
py -3 tools/verify_v06.py --require-qt --full
py -3 run_studio.py
```

On Linux where `liblua5.4` is available, host-only tests may use:

```bash
python tools/verify_v06.py --system-lua
python tools/virtual_phone_cli.py projects/lua-snake/main.lua -o build/snake-live.png --frames 14
```

Source ZIP excludes host binaries, private signing keys and generated build
data. Build toolchain and Qt are installed on each developer's PC. No code
from LuaS30-IDE or vendor MediaTek SDK is bundled into the IDE.
