# v0.6 Verification

The release gate must run on the delivered source. See companion report
`QEAPP_Studio_v06_Verification_Report.md` in the release package. Tests include
real C++ interactive Lua host frame streaming and old deterministic/beta tests.

- `python -m unittest discover -s studio/tests -v`
- `python tools/verify_v05.py --system-lua` on Linux with system Lua (host only)
- `python tools/virtual_phone_cli.py projects/lua-snake/main.lua -o build/virtual-snake.png --frames 14`
- `python -m py_compile studio/gui/window.py studio/gui/virtual_phone.py`

Qt GUI smoke is optional and must actually run on a machine with PySide6.
Host preview is not hardware validation. Do not claim PlatformIO/board tests.
