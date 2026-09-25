# M0 Verification Report — 2026-09-25

Target source used for inspection: VQEAF OS v2.4.2 local full-source archive corresponding to GitHub commit `909f8cf` (git tree unchanged for app contracts). LuaS30-IDE source consulted for Studio/engine organizational pattern; no MediaTek SDK or VXP toolchain used.

Actual checks:

- PASS: `qstudio doctor --firmware-root <VQEAF-OS source>`; original signer, verifier/service headers and signing docs present.
- PASS: `qstudio validate projects/text-notes` and `projects/web-bookmark`.
- EXPECTED REJECT: `qstudio validate projects/snake-lua-proposal`: `NOT_IMPLEMENTED` (Lua game engine not yet integrated).
- PASS: 6/6 Python unit/host integration tests, including temporary P-256 key signing using **the original** `VQEAF-OS/tools/build_qeapp.py`, two real QEAPP/2 packages (web + text), opt-in P-256 signature verification, tamper/wrong key-id rejection, schema validation and init template.
- NOT DONE: actual PySide6 IDE, host Lua runtime, QEAPP/3 packer, ESP32-S3 PlatformIO cross-build, flash/hardware test.

The private fixture signing key existed solely in `TemporaryDirectory()` during the test. It is not included in the ZIP or repository. Device firmware still must pin your real public key matching production signed apps. Host signature verification is performed against the PEM supplied by the user, not implicitly against the device's trust key.

---

# M1 host verification — 2026-09-25, kit v0.2

**Nguồn:** v0.1 developer kit + C++17 engine M1 trong thư mục này. Dùng cùng mã core để chạy hai demo Snake game / Hello application. Không thay đổi VQEAF firmware.

Kết quả quan sát trong môi trường kiểm tra:

- **PASS 12/12:** `QEAPP_FIRMWARE_ROOT=<VQEAF OS v2.4.2 checkout> python3 -m unittest discover -s tests -v`. Trong đó signer E2E dùng `cryptography` + P-256 private fixture nằm trong temporary directory, build/inspect signed text + web QEAPP/2 và kiểm tamper/key-id.
- **PASS:** C++17 `g++` và `clang++` `-Wall -Wextra -Werror -pedantic` chạy `tests/test_engine.cpp` (lifecycle, bounded fixed timestep, clipping, invalid sprite, reserved HOME/SELECT, input queue full, clock wrap, pause/resume).
- **PASS:** `g++ -fsanitize=undefined` cho bộ test engine C++; không thấy UBSan runtime error.
- **PASS:** 5 golden SHA-256 trong `tests/golden/host_sha256.json` từ 240x320 host renderer trùng khớp hoàn toàn; PNG xuất qua Python stdlib zlib, không phải ảnh AI vẽ tay.
- **PASS:** 1.200 host tick (50ms/tick = 60 giây **thời gian mô phỏng**), không crash; `input_overflows=0` với replay mặc định. Đây là smoke/soak vòng runtime, không bảo đảm game không Game Over trong 60 giây.
- **PASS:** `doctor` nhận nguồn firmware QEAPP/2, `validate` hai mẫu web/text; **EXPECTED REJECT**: project Lua proposal, vì thiếu runtime.

**Giới hạn chưa kiểm tra:** không có test Windows cho file `.bat`; chưa làm PySide6 GUI, GPIO adapter, ST7789 DMA, sound, PSRAM profiling, PlatformIO/cross-build, board real screenshot hoặc ký game/app Lua C++ độc lập `.qeapp`. Golden hash chỉ chứng minh render host ổn định trong điều kiện test, không chứng minh màu trên panel thật. Chữ ký kiểm với public fixture do test tạo; firmware thiết bị cần ghim public key thật của nhà phát hành.
