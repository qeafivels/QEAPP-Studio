# Role: Studio GUI & Launcher

**Own:** `studio/gui/`, `studio/core/` GUI-facing pieces, `studio/main.py`, Windows launcher and update probes. Coordinate edits touching `studio/gui/virtual_phone.py` with Lua agent.

**Must preserve:** workspace sandbox/atomic save, one authoritative CLI build, optional Qt dependency, deterministic status of launched QProcess, no private key in logs. Update via staging environment + `pip check` + *real offscreen* `QApplication` probe + rollback pointer.

**Required gates:** `python -m unittest discover -s studio/tests -v`; `run_studio.bat --gui-check` **on Windows with PySide6**, plus screenshot/log from actual Qt probe. On Linux use `QT_QPA_PLATFORM=offscreen python tools/gui_post_update_check.py ...` if Qt exists. If absent, report GUI `NOT_RUN` and code/static tests separately.

**Do not:** redesign firmware theme when asked to change desktop UI, mark illustrative mockup as Qt screenshot, or repair Python by deleting user files.
