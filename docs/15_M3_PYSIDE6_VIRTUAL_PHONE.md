# QEAPP Studio v0.6 — M3 desktop workspace + interactive virtual phone

## Implemented (PC)

This release redesigns the **PySide6 UI** as an independent dark indigo/purple
multi-pane IDE. Its **interactive virtual phone** runs the project's Lua source
in the **same restricted `QeLuaRuntime.cpp`** used by the PC host-preview and
ported into the experimental ESP32-S3 beta firmware. It is **not** a binary
emulator for ESP32, Symbian, MRE, ST7789, microSD, Wi-Fi or the firmware app
installer. The Lua firmware port and on-device execution are still beta and
have not been verified on physical hardware in this release.

The layout is inspired by established editor concepts (activity rail,
Explorer, multi-tab editor, bottom diagnostics, device pane) used in
LuaS30-IDE, but is new implementation, not an imported UI, icon pack or code
from that project.

### Workflow

1. Install Python 3.11+, PySide6 and optional signing tools:

   ```powershell
   py -3 -m pip install -r requirements-studio.txt
   py -3 run_studio.py
   ```

2. **File → New Lua App (Beta)** or **New Pixel Sprite Game (Beta)**.
   Use Explorer and editor to change `main.lua` and assets.
3. Press **F6 Validate** before build; **F9** runs the live phone on PC.
   First run compiles `build/qe_lua_host` from C++ shared VM. On Windows,
   bootstrap **official Lua upstream** first:

   ```powershell
   py -3 tools/bootstrap_lua.py
   py -3 tools/build_lua_host.py
   ```

   Internet is used only to obtain pinned Lua source, not by the guest app.
   Without Internet, use `bootstrap_lua.py --archive <trusted tarball>`.
4. Click phone's **D-Pad / START / OPTION** or focus the phone and use keyboard
   arrows, Enter and Escape. Click MENU/A/B to leave the guest (host UI shell).
   SELECT changes the host indicator; T9 guest input remains unimplemented.
5. **PNG** exports the most recent 240×320 host frame (including host-only
   status/soft-key shell). FPS badge is PC frames delivered to Qt, capped around
   15 FPS; **not real ESP32 FPS**.
6. **F8** renders a deterministic Lua replay using the original CLI and
   `tests/input_replay.json`; this is separate from the live phone.
7. **F7** builds signed `.qeapp` through the existing firmware signer after
   explicit signing key selection. Lua packages require separately provisioned
   `vqeaf_lua_beta` firmware and matching public key; **no unsigned bypass**.

### Screen, input and virtual hardware

- Host wire format: `QEFRAME <n>\n` + exactly 129,600 little-endian bytes
  for a 240×270 RGB565 guest buffer. Studio composes a separate 29px header
  and 21px footer for a total 240×320 virtual phone.
- Commands over local process stdin: `TICK <1..100>`, `KEY <name> <0|1>`, `QUIT`.
  Valid guest keys: `up/down/left/right/start/option`. MENU/A/B are consumed
  by desktop shell and **cannot escape into guest code**.
- Guest source ≤64 KiB, VM heap ≤192 KiB, existing instruction/deadline,
  draw-call quotas and a 5-second desktop response watchdog. A 30-frame metric
  sample is printed by the native process on stderr.
- QProcess and QTimer ensure all VM work is off the GUI thread; only one tick
  can be pending. No arbitrary shell commands are accepted from Lua.
- Phone and deterministic PNG replay use the **actual Lua VM**; they are not
  screenshots of the ESP32 firmware GUI or a `.qeapp` installer emulator.

### Code map

| File | Responsibility |
|---|---|
| `studio/gui/window.py` | redesigned window, splitters, toolbar, menus, Explorer, tabs and jobs |
| `studio/gui/theme.py` | new consistent QSS dark indigo theme |
| `studio/gui/virtual_phone.py` | native Qt phone shell, host VM, D-pad, screenshot and FPS badge |
| `studio/core/frame_protocol.py` | bounded binary stream parser independent of Qt |
| `runtime/host/qe_lua_host.cpp` | `--interactive` persistent guest mode; existing batch remains compatible |
| `tools/virtual_phone_cli.py` | test same guest/protocol headlessly, export real Lua frame |
| `studio/tests/test_virtual_phone.py` | chunking, corruption, keyboard restrictions and host smoke |

### Command-line smoke without PySide6

```bash
# Only on Linux systems with system liblua5.4 (host smoke ONLY):
python tools/build_lua_host.py --system-lua
python tools/virtual_phone_cli.py projects/lua-snake/main.lua -o build/phone.png --frames 14
python -m unittest discover -s studio/tests -v
```

### Remaining work

- Native PySide6 interaction **must still be tested on a Windows machine with
  PySide6 installed**; the current runner did not have Qt packages.
- The host renders the Lua app portion only; firmware Home/Menu, signed package
  installation, theme manager and peripherals are not emulated.
- End-to-end `vqeaf_lua_beta` on ESP32-S3 still needs PlatformIO/hardware tests;
  host FPS does not demonstrate ST7789 performance.
- Add debugger/breakpoints, code intelligence, full build error navigation and
  sprite/tilemap editors as subsequent dedicated milestones.

## Attribution / licensing

LuaS30-IDE is a workflow reference only. The new QEAPP Studio GUI, stream
protocol and device frame shell are independently implemented and do not bundle
LuaS30 artwork or the proprietary MRE SDK. Official Lua source, when
bootstrapped, retains its own upstream license.
