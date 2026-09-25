> **REPOSITORY ĐỘC LẬP:** QEAPP-Studio đã tách khỏi VQEAF-OS. Xem [README_SEPARATE_REPOS.md](README_SEPARATE_REPOS.md). Các đường dẫn `firmware/VQEAF-OS` xuất hiện trong ghi chú phiên bản cũ là **đường dẫn lịch sử**; hiện dùng biến `QEAPP_FIRMWARE_ROOT` hoặc clone hai repo cùng thư mục cha. Không đóng gói firmware trong Studio.

# QEAPP Studio v0.7.4 — Safe GUI Verified Updates

`run_studio.bat` now performs real **offscreen StudioWindow GUI verification** and
**safe staged dependency updates**. It never overwrites the working Python
environment in place: an updated environment becomes active only after its
actual Qt/Explorer/editor/Virtual Phone smoke test passes.

Windows quick start:

```bat
run_studio.bat                  REM safe daily update + GUI
run_studio.bat --update-now     REM stage, verify, activate, GUI
run_studio.bat --gui-check      REM GUI test + genuine offscreen PNG; no update
run_studio.bat --rollback-update
run_studio.bat --offline
```

The verification screenshot and JSON appear under `logs/gui-check-*.png/json`
**only if real Qt runs successfully**. See
`docs/17_SAFE_GUI_UPDATES_v074.md` for rollback, fail-safe rules and limits.
No change to the firmware .qeapp install format or device-runtime claims.

---

## AI Agent workflow (documentation kit v1.0)

This source tree includes an AI Agent onboarding system: `AGENTS.md` → `PROMPT.md` → `SKILLS.md`, specialist roles in `agents/`, architecture and verification templates in `docs/agents/`. Run `python tools/validate_agent_docs.py` to verify the instructions match the actual source layout. These files change **documentation only**: they do not change Studio, firmware or the original VQEAF OS Retro-Go visuals. The bundled firmware snapshot may be older than the separate VQEAF OS Back r2 release.

---


## Windows — tự động kiểm tra thư viện và chạy GUI (v0.7.3)

Giải nén mã nguồn ZIP. Nhấp đúp `run_studio.bat`. Launcher kiểm tra Python 3.10+
64-bit, tạo `.venv` nếu cần, kiểm tra PySide6/Pillow/cryptography + `pip check`,
tự cài các thư viện thiếu và thử cập nhật phiên bản tương thích mỗi 24 giờ.
Sau khi Qt offscreen smoke đạt sẽ mở IDE; mạng lỗi vẫn mở nếu thư viện đã cài
và kiểm tra đạt. Lưu log tại `logs/launcher.log` và `logs/gui-crash.log`.

Lệnh tùy chọn: `run_studio.bat --offline`, `run_studio.bat --update-now`,
`run_studio.bat --no-update`, `run_studio.bat --diagnose`, `run_studio.bat --repair`.
Máy ảo Lua host cần toolchain riêng; tải Lua có SHA256 theo chỉ dẫn
`run_studio.bat --setup-lua --build-vm`. Xem hướng dẫn chi tiết tại
`docs/19_V073_WINDOWS_AUTO_UPDATE_LAUNCHER.md`.

---

# QEAPP Studio v0.7.2 — IDE + Lua Host VM + GUI Diagnostics + Safe Repair

Môi trường viết game/app Lua cho **VQEAF OS**: editor PySide6, công cụ build/inspect signed `.qeapp`, trình thử game Lua trên PC, và firmware **beta** ESP32-S3 N16R8 dùng chung mã runtime C++. Bản v0.5 giữ recorder/input guards của v0.4.1 và thêm `engine.blit1` (mask 1-bit), PNG→Lua converter, template sprite game và PNG preview an toàn trong Explorer.

**Phân biệt mức độ:** `type=web`/`type=text` được firmware VQEAF OS v2.4.2 hỗ trợ. `type=lua` **chỉ** dành cho firmware thử nghiệm `vqeaf_lua_beta` dùng khóa ký độc lập; chưa build PlatformIO, nạp hay thử nghiệm runtime Lua trên thiết bị thật. Ảnh mô phỏng PC không phải ảnh chụp ST7789. Đây không phải giả lập Symbian/MRE.

## Cấu trúc

```text
QEAPP-Studio-v0.7.2/
├── PROMPT.md / SKILLS.md                     # Hợp đồng cho AI Agent
├── docs/{01..12}*.md                         # ABI, bảo mật, build/kiểm thử
├── run_studio.py / run_studio.bat             # Desktop IDE PySide6
├── studio/
│   ├── core/{workspace,jobs,commands,config,replays}.py
│   ├── gui/window.py                         # Explorer, Lua editor, recorder, Build/Run
│   └── tests/                                # Core + tùy chọn GUI offscreen
├── engine/                                   # M1 native C++ host renderer
├── runtime/
│   ├── include/QeLuaRuntime.h                # API portable Lua 5.4
│   ├── src/QeLuaRuntime.cpp                  # MỘT source dùng chung host & firmware
│   └── host/{qe_lua_host.cpp,compat/,tests/}
├── firmware/VQEAF-OS/                        # v2.4.2 + opt-in Lua beta overlay
│   ├── src/lua/                              # Mirror của runtime/src (feature-gated)
│   ├── lib/VqeafLua54/                       # Cài upstream Lua bằng bootstrap_lua.py
│   └── platformio.ini                        # env:vqeaf_os và env:vqeaf_lua_beta
├── projects/{lua-hello,lua-snake,text-notes,web-bookmark}/
├── tools/{qstudio,bootstrap_lua,build_lua_host,lua_preview,...}.py
└── tests/                                    # Regression/signature/security
```

## Chạy trên Windows

Yêu cầu Python 3.10+, Windows 10/11 x64, PySide6 cho GUI, GCC/MinGW/Clang cho host nếu muốn tự biên dịch VM, và `cryptography` để ký gói.

```powershell
py -3 -m pip install -r requirements-studio.txt
py -3 run_studio.py
```

Trong IDE: `File → New Lua App (Beta)` hoặc `New Pixel Snake Lua Game (Beta)`. Chỉnh `main.lua`; dùng khu **GAMEPAD REPLAY** để thêm sự kiện `start/up/down/left/right/option` tại frame chỉ định, nhấn **Save Replay JSON**, sau đó **F8**. Preview 240×320 là giả lập PC. **F6** validate; **F7** build signed QEAPP/2 sau khi đã tự tạo khóa ký beta và chọn đường dẫn firmware.

## Xây Lua host runtime

```powershell
py -3 tools/bootstrap_lua.py
py -3 tools/build_lua_host.py
py -3 tools/qstudio.py lua-preview projects/lua-snake --frames 8 --replay tests/input_replay.json -o build/snake-lua.png
```

`bootstrap_lua.py` tải Lua 5.4.8 chính thức, xác minh **SHA-256 ghim cứng** trước khi chép mã nguồn và LICENSE vào `firmware/VQEAF-OS/lib/VqeafLua54`. Offline: `--archive C:\Downloads\lua-5.4.8.tar.gz`. Chưa vendor Lua nguồn vào ZIP: cần bootstrap thành công trên máy phát triển. Trên Linux có `liblua5.4.so.0`, `build_lua_host.py --system-lua` là đường thử nghiệm PC, **không** thay cho Lua upstream khi release firmware.

## Tạo khóa và build beta firmware (chưa xác nhận trên board)

```powershell
py -3 tools/provision_lua_beta_key.py --private C:\SecureKeys\vqeaf-lua-beta-private.pem
pio run -d firmware\VQEAF-OS -e vqeaf_lua_beta
```

Chỉ public key được thêm vào firmware beta; **không bao giờ đưa private PEM vào repository, thẻ SD hoặc ảnh chụp/log**. Stock firmware không được đổi trust key. Trong beta profile, publisher beta là trust anchor duy nhất: những gói `text/web` cũ ký bằng key production có thể bị từ chối. Sao lưu khóa beta nếu còn cần cài lại gói đã phát hành.

Đóng gói `.qeapp` Lua sau khi đã provision key:

```powershell
py -3 tools/qstudio.py build projects/lua-snake --experimental-lua --firmware-root firmware/VQEAF-OS --sign-key C:\SecureKeys\vqeaf-lua-beta-private.pem --key-id 0x544c5541 -o dist/snake-lua.qeapp
py -3 tools/qstudio.py inspect dist/snake-lua.qeapp --public-key C:\SecureKeys\vqeaf-lua-beta-private_public.pem --key-id 0x544c5541
```

Chỉ cài trên firmware **beta đã nạp đúng public key**: chép vào microSD `/System/Apps/Inbox/`, mở App Installer; không tắt signature check để cài. `type=lua` chạy như text source giới hạn 64KiB, không được cấp quyền truy cập tuỳ ý file/network/SD. Firmware `vqeaf_os` bình thường vẫn từ chối ứng dụng Lua.

## Kiểm thử

```powershell
py -3 -m unittest discover -s studio/tests -v
py -3 -m unittest discover -s tests -v
py -3 tools/test_lua_beta_host.py
py -3 firmware/VQEAF-OS/tools/verify_v242.py
```

Đặt `QEAPP_FIRMWARE_ROOT=firmware/VQEAF-OS` (theo cú pháp shell đang dùng) nếu muốn suite chạy kiểm thử signer thực. Test GUI offscreen chỉ chạy khi máy đã cài PySide6; báo SKIPPED **không** được gọi PASS. Kết quả trong bản phát hành: `docs/11_VERIFICATION_V041.md`.

**Đọc tiếp:** `docs/10_LUA_BETA_ARCHITECTURE.md`, `docs/12_INPUT_REPLAY.md`, `PROMPT.md`, `SKILLS.md`.

## Tính năng v0.5: pixel sprite đơn sắc

- `File → New Sprite Lua Game (Beta)` hoặc `python tools/qstudio.py init --template lua-sprite --id new_game --name "New Game" -o new-game`.
- PNG 1..32 pixel/chiều → `tools/pixel_sprite.py` → Lua source; Lua VM có `engine.blit1`. Double-click PNG trong Explorer để preview (không mở binary bằng editor UTF-8).
- Tài liệu: `docs/13_SPRITE_AND_LUA_WORKFLOW_V05.md`.
- Host gate một lệnh: `python tools/verify_v05.py --system-lua` (Linux chẩn đoán) hoặc bootstrap upstream Lua rồi `python tools/verify_v05.py --require-qt`. Kết quả trong `build/reports/v05/`.
- Đường firmware beta vẫn là bản thử nghiệm; *không* cam kết chạy trên ESP32-S3 khi chưa có build PlatformIO và log thật.

## v0.6 — PySide6 M3 workspace + interactive host virtual phone

The desktop is now organized into activity rail, searchable Explorer, multi-tab
code editor, command palette, bottom output, and a right **interactive 240×320
virtual phone**. Press **F9** to start a real bounded PC Lua VM; click its
physical keypad to send allowed app events. **F8** keeps the deterministic
replay renderer. Export the host screen via PNG. The visual theme is original
indigo/violet and uses standard PySide6 widgets.

**Important:** The virtual phone is a Lua *host runtime*, not an ESP32-S3,
Symbian/MRE, microSD/WiFi or system installer emulator. A signed Lua QEAPP/2
still requires firmware `vqeaf_lua_beta` with the appropriate publisher key;
no ESP32-S3 benchmark or hardware success is claimed here.

See [`docs/15_M3_PYSIDE6_VIRTUAL_PHONE.md`](docs/15_M3_PYSIDE6_VIRTUAL_PHONE.md).


## v0.7 — UI nâng cấp, search và máy ảo có điều khiển

Nguồn v0.7 giữ nguyên cấu trúc v0.6 và bổ sung code editor có số dòng,
Find/Replace/Go To, Search entire project, thanh Problems và máy ảo Pause/Step,
FPS 15/30 host timer cap cùng bộ thống kê FPS/response/guest render/heap.
Chạy Windows GUI:

```powershell
py -3 -m pip install -r requirements-studio.txt
py -3 tools/bootstrap_lua.py
py -3 tools/verify_v07.py --require-qt
py -3 run_studio.py
```

Xem [docs/16_V07_WORKBENCH_AND_VIRTUAL_PHONE.md](docs/16_V07_WORKBENCH_AND_VIRTUAL_PHONE.md).
Qt offscreen và PlatformIO/ESP32 chưa xác minh trong môi trường Linux tạo bản này.

## v0.7.1 — launcher tự kiểm tra Windows

Double-click `run_studio.bat`: tự kiểm tra Python 3.10+, tạo `.venv`, cài thiếu
PySide6/cryptography/Pillow, kiểm tra Qt offscreen, dò công cụ biên dịch Lua VM
và mở GUI. Tệp `logs/launcher.log` và `logs/gui-crash.log` hỗ trợ chẩn đoán.
Xem `docs/17_WINDOWS_LAUNCHER_V071.md` cho tùy chọn `--no-install`,
`--check-only`, `--setup-lua`, `--build-vm` và xử lý lỗi.

## v0.7.2 — Debug VM, inspect GUI và sửa lỗi an toàn

**IDE**: nút Activity dùng system icons; có menu Tools và bảng Diagnostics/VM Inspector,
Errors/Problems dẫn đến đúng dòng Lua khi host có đủ thông tin.
**VM**: FPS cap 15/30/60 (timer cap, không phải FPS đo được), heap 96/192/384 KiB,
Pause/Step/Restart và hai API chỉ đọc `engine.heap_used()` / `engine.heap_peak()`.
**Kiểm tra/sửa lỗi**: `run_studio.bat --diagnose` chỉ xem; `--repair`
backup cấu hình JSON lỗi / `.venv` lỗi, không xóa mã dự án hay private PEM.
`--reinstall-deps` phải yêu cầu rõ để buộc cài lại toàn bộ thư viện.
**Debug Session**: tùy chọn log sự kiện giới hạn trong `logs/vm-*.jsonl`,
không lưu nội dung script/secret. Chi tiết: `docs/18_V072_VM_IDE_GUI_DIAGNOSTICS_SAFE_REPAIR.md`.

Máy ảo là trình chạy Lua **trên PC** (giới hạn tài nguyên, không có SD/WiFi/SoC),
không phải giả lập toàn bộ ESP32-S3. Chưa xác nhận bản GUI mới trên Windows
và firmware beta trên thiết bị thực.
