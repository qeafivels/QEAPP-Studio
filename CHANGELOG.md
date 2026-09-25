# v0.7.4 — 2026-09-25

- Staged non-relocating virtualenv updates and atomic runtime activation.
- Offscreen test of real IDE window, temporary project, Explorer, editor and 240x320 phone screen after dependency updates.
- Fail-safe fallback / validated manual rollback / immediate GUI startup auto-rollback.
- Exclusive update lock, read-only `--gui-check` and machine-readable diagnostics.
- No ESP32-S3 hardware verification claims.

# CHANGELOG — QEAPP Studio

## 0.7.3 (2026-09-25) — auto-update Windows launcher
- feat(launcher): verify local versions and run `pip check` on every GUI start; automatically install missing/inconsistent desktop dependencies into isolated `.venv`.
- feat(updates): check for compatible package updates once every 24 h (failed attempts back off six hours), with SHA-256 requirements file and Python interpreter cache keys; no install outside `.venv` by default.
- feat(control): `--update-now`, `--no-update`, `--offline`; read-only `--check-only`/`--diagnose` retained; `--system` never silently upgrades global Python.
- feat(resilience): failed periodic online update does not block GUI if local versions, dependency integrity and Qt smoke still pass; errors logged under `logs/launcher.log`.
- scope: host PC Python package update only; no implicit Lua upstream download, flashing, firmware or signed `.qeapp` changes. Windows interactive validation remains to be done on target PC.

## 0.7.2 (2026-09-25)
- feat(vm): bounded interactive Lua host heap selection (96/192/384 KiB), heap usage APIs and 10-frame counters.
- feat(ide): native Qt activity icons, VM inspector, errors-to-source diagnostics and restart.
- feat(debug): opt-in local JSONL VM tracing without script/credentials; process exception capture.
- feat(repair): read-only doctor and explicit backup-before-repair settings / broken venv; separate forced pip reinstall.
- test: real Lua 60-frame host replay, security, runtime and legacy regressions.
- limitations: PySide6 GUI test only runs if installed; no device claims.

## v0.7.1 — Windows launcher robustness (2026-09-25)

- fix(launcher): detect Python 3.10+, quote Python paths and propagate real exit status.
- feat(launcher): isolated venv, missing-dependency install, PySide6 Qt offscreen smoke, diagnostic logs and rotation.
- feat(vm): report Lua source/compiler/host binary; optionally bootstrap verified Lua and rebuild host runner; platform-specific .exe output.
- test: stdlib launcher tests; preserve original projects/signing/GUI; Windows execution remains to be verified.

## v0.7.0 — Developer Workbench & Host VM Controls (2026-09-25)

- fix(gui): import QFrame in StudioWindow startup; no broken Qt constructor due to missing widget import.
- feat(ui): separate Explorer and project-wide Search; menu Edit/Run/View; Output + Problems; persist bottom-panel visibility; text-labelled action controls.
- feat(editor): gutter line numbers/current line, Find/Replace, Go to Line, Ln/Col status.
- feat(core): bounded filesystem-safe UTF-8 search including dirty editor buffers.
- feat(vm): pause, resume, single frame stepping and 15/30 FPS host caps; measured host round-trip response; VM heap/guest render diagnostic parsing.
- feat(host): deterministic QEHOST_METRIC render_us (30-frame moving block) and headless PNG/metrics JSON.
- test: new search/parser tests, 30-frame real VM metric test, Qt-optional workbench smoke, verify_v07.py.
- scope: PC host regression PASS, GUI requires PySide6 offscreen validation on Windows; no ESP32 hardware claim. Preserve signed QEAPP/2 and Lua beta trust policy.

## v0.5.0 — Lua Pixel Sprite IDE / bounded runtime (host validated)

- New `engine.blit1`: 1-bit sprite mask row-major/MSB-first 1..32 px; clip to 240×270 game area, transparent pixels and 512 draw calls/frame preflight; mirrored source host & firmware beta.
- New `tools/pixel_sprite.py`: bounded PNG→inline Lua packed mask converter, alpha/dark/light threshold, Pillow 10–12 compatible. Assets remain design-time; no runtime file/SD permissions.
- New `projects/lua-sprite`, CLI `init --template lua-sprite`, GUI New Sprite Game and Insert Pixel Sprite PNG.
- New safe .png Explorer preview, with guarded path, max 1 MiB and dimensions ≤512; the binary editor remains inaccessible.
- Added `tests/test_sprite_v05.py`, `studio/tests/test_png_preview.py`, repeatable `tools/verify_v05.py` and detailed workflow documentation.
- Verification covers host Python/C++ VM, actual signer regression and host-stub firmware beta linker. No real PlatformIO build/board screenshot; PySide6 not installed in release host, GUI remains unverified until Windows/offscreen tests.

# Changelog

## v0.2 — M1 portable host engine

- Implement C++17 `qe::Runtime`, `qe::App` lifecycle, fixed-step timer cap, 32-event input queue, reserved OS keys.
- Implement clipped RGB565 draw, bounded sprite lookup and minimal 3x5 text.
- Implement PC HostCanvas 240x320, two demos `Pixel Snake`/`Hello`, deterministic replay and PNG screenshot exporter (Python stdlib).
- Extend `qstudio simulate`; retain strict QEAPP/2 `web/text` signed package workflow and reject `lua-proposal`.
- Add C++/Python tests, 5 golden screenshot hashes, simulated 1.200-step soak and optional actual firmware signer regression.
- Add `docs/07_M1_HOST_ENGINE.md` and M2 GUI implementation plan, update PROMPT.md / SKILLS.md.
- Scope: HOST ONLY. No firmware integration, independent native or Lua `.qeapp` packaging, or hardware test.

## v0.1 — QEAPP Studio Developer Blueprint (documentation + M0 CLI)

- Định nghĩa PROMPT.md, SKILLS.md, quy trình 10 bước, package contract QEAPP/2 và roadmap runtime Lua/QEAPP format mới.
- Tạo project templates `text-notes`/`web-bookmark` (buildable with firmware signer) và `snake-lua-proposal` (explicitly unbuildable).
- M0 `tools/qstudio.py` hỗ trợ doctor/validate/build/inspect; verify chữ ký opt-in với public PEM, không ghi private key.
- Bộ unittest kiểm tra schema, path traversal, HTTPS policy, missing Lua runtime, temporary-key signer end-to-end và tampering.
- Chưa thêm IDE GUI hoặc Lua runtime, chưa build firmware hay nạp ESP32-S3.

## v0.3 — M2 Desktop IDE core alpha (2026-09-25)

- NEW `studio/core/workspace.py`: bounded sandboxed UTF-8 source editing, symlink/key/build path deny rules, atomic save with conflict detection and safe mkdir.
- NEW `studio/core/jobs.py`: streaming subprocess runner; cancellation for process trees on Windows/POSIX, timeout, log secret-path masking and concurrent-job guard.
- NEW `studio/core/config.py`, `studio/core/commands.py`: user-level settings whitelist without signing credentials; typed wrappers for original qstudio CLI.
- NEW `studio/gui/window.py`: PySide6 project Explorer, editor, F6 validate, F7 signed text/web build, inspect, host Snake/Hello preview, output panel, Stop and firmware selector.
- NEW `run_studio.py`, `run_studio.bat`, `requirements-studio.txt`, unit and optional offscreen GUI tests.
- M1 C++17 engine, QEAPP2 signer flow, golden reference tests and M0 project templates preserved unchanged.
- LIMITATION: PySide6 is not installed in release build environment; offscreen tests SKIPPED. Host C++ tests run, but firmware build/device runtime not tested.

## v0.6 — M3 UI and persistent PC Lua virtual phone
- Rebuilt PySide6 workbench as activity rail / searchable Explorer / editor +
  diagnostics / right device emulator with original indigo-violet QSS.
- Added command palette, Quick Open, Find and project-independent host runner.
- Added persistent interactive Lua host protocol with bounded RGB565 frame
  parsing, D-pad events, frame watchdog, screenshots and host FPS badge.
- Added headless real-VM smoke and protocol rejection tests.
- Kept QEAPP/2 signing and experimental firmware gate unchanged.
- Windows PySide6 and real ESP32 board not verified in current environment.
