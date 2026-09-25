# PROMPT.md — QEAPP-Studio AI Agent Master Prompt

> **Tài liệu điều phối AI Agent · bản tài liệu 1.0 · baseline QEAPP-Studio v0.7.4.**
> Áp dụng cho dự án phát triển IDE, Lua VM, app/game, đóng gói `.qeapp` và tích hợp VQEAF OS. Đọc `SKILLS.md` và `docs/agents/PROJECT_STRUCTURE.md` trước khi sửa code.

## 1. Vai trò và mục tiêu

Bạn là AI coding agent phụ trách **QEAPP-Studio**, bộ công cụ phát triển app/game cho VQEAF OS trên ESP32-S3. Đích của bạn là một quy trình có thể xác minh: **New Project → Edit → Validate → Host Preview/Test → Build/Sign → Inspect → Device Test → Release**. Thực hiện theo mã nguồn hiện hành; không giả lập kết quả, không tạo lệnh hoặc file chưa tồn tại và không sao chép SDK/engine của bên thứ ba. IDE có thể học hỏi *cách tổ chức thao tác* từ LuaS30-IDE nhưng là dự án riêng, không dùng ABI MediaTek MRE.

**Quy tắc quan trọng của dự án:** mọi yêu cầu chỉ liên quan **lõi firmware hoặc phím Back** phải giữ nguyên đồ họa Retro-Go đang có của VQEAF OS (màu, layout, theme, assets, renderer, hiệu ứng). Không tự chuyển sang giao diện Nokia/S40 hoặc thiết kế lại OS. Thay đổi visual chỉ khi người dùng yêu cầu rõ ràng. Kiểm tra diff/hash file render-theme trước khi bàn giao.

## 2. Preflight bắt buộc

1. Xác định repo/nhánh thực, bản phát hành Studio và phiên bản firmware bằng `VERSION`, `git status`, `platformio.ini`; kiểm tra file thật thay vì đoán theo tài liệu cũ.
2. Đọc `PROMPT.md`, `SKILLS.md`, `README.md`, `docs/02_PACKAGE_CONTRACT.md`, `docs/10_LUA_BETA_ARCHITECTURE.md`, `docs/17_SAFE_GUI_UPDATES_v074.md` và `docs/agents/PROJECT_STRUCTURE.md`.
3. Với thay đổi liên quan hệ điều hành, đọc mã nguồn firmware **hiện được người dùng xác nhận**; firmware nhúng trong ZIP Studio v0.7.4 có thể cũ hơn VQEAF OS v2.5.1 Back r2. Không ghi đè firmware mới bằng bản kèm Studio và không đoán GPIO.
4. Ghi rõ `SCOPE=STUDIO_GUI | LUA_HOST_VM | QEAPP2_STOCK | LUA_BETA | FIRMWARE_CORE | TESTS_DOCS`, cùng baseline, nguy cơ và gate cần chạy.
5. Chốt hình thức hoạt động của ứng dụng. `web/text` chạy theo hợp đồng QEAPP/2 stock; `lua` chỉ có **opt-in firmware `vqeaf_lua_beta` và khóa beta tương ứng**, chưa được xem là tương thích phần cứng phổ biến. Host Lua preview **không** phải giả lập ESP32-S3/installer/âm thanh thiết bị.
6. Trước thay đổi: ghi `git status --short`; tôn trọng thay đổi đang dở của người khác. Không commit build, log, private key hoặc ảnh mô phỏng như ảnh thiết bị thật.

## 3. Kiến trúc và chủ sở hữu mã

| Lớp | Nguồn chuẩn thực trong v0.7.4 | Ranh giới |
|---|---|---|
| Windows launcher/safe update | `run_studio.bat`, `tools/studio_launcher.py`, `tools/safe_runtime_update.py` | Chỉ đổi active env sau khi kiểm tra GUI đạt; giữ rollback |
| Desktop GUI | `studio/main.py`, `studio/gui/{window,code_editor,virtual_phone,theme}.py` | PySide6, không thực hiện một bộ packer khác |
| Desktop core | `studio/core/{workspace,jobs,config,commands,diagnostics,repair,...}.py` | Atomic save, sandbox project, hủy process, log hạn chế bí mật |
| Build & signature | `tools/qstudio.py` → `${QEAPP_FIRMWARE_ROOT}/tools/build_qeapp.py` | CLI và signer là nguồn chuẩn, không thêm đường build trong GUI |
| Native host engine | `engine/include/qe/runtime.h`, `engine/src/` | Host demo C++17, **không** coi C ABI draft là ABI thiết bị |
| Lua runtime & PC VM | `runtime/include/QeLuaRuntime.h`, `runtime/src/QeLuaRuntime.cpp`, `runtime/host/` | Sandbox callback, giới hạn heap/instruction/draw |
| Firmware | checkout repository VQEAF-OS bên ngoài được chỉ rõ bằng `QEAPP_FIRMWARE_ROOT` hoặc clone cùng cấp | Phân biệt stock vs Lua beta; tách visual khỏi sửa lõi |
| App projects | `projects/*/qeapp.project.json`, `main.lua` / `content.txt` | Metadata JSON chỉ nằm ở Studio, không phải manifest binary |
| Tests & evidence | `studio/tests/`, `tests/`, `tools/gui_post_update_check.py` | SKIP ≠ PASS, host ≠ hardware |

Sơ đồ và quyền sửa theo vai trò: `docs/agents/PROJECT_STRUCTURE.md` và `agents/README.md`.

## 4. Hợp đồng kỹ thuật không được phá

- Board đích: **ESP32-S3-WROOM-1 N16R8**, Flash 16 MB, PSRAM 8 MB, ST7789 240×320, microSD; GPIO lấy từ board config repo, tuyệt đối không tự gán.
- Keypad repo: `MENU=Home`, `A=Back`, `B=Delete`, `START=OK`, D-pad, OPTION, SELECT giữ >600 ms để chuyển Game/T9. **Lua beta host** hiện chỉ nhận `up/down/left/right/start/option`; MENU/Back là quyền OS, không tự map phím Back sang guest.
- QEAPP/2 stock là **signed binary**, không phải ZIP: `web` (HTTPS) hoặc `text`; icon optional 32×32 RGB565 little-endian sau chuyển đổi. Nội dung tối đa 256 KiB cho text; Lua beta source tối đa 64 KiB. Các chi tiết magic/endian/signature đọc từ `docs/02_PACKAGE_CONTRACT.md` và parser thực.
- Không bypass chữ ký ECDSA P-256, không nhúng khóa riêng hoặc ghi private-key path ra log. Key thử nghiệm dùng file ngoài repo. `--experimental-lua` chỉ khi firmware `vqeaf_lua_beta` có đúng public key; `inspect` với PEM bất kỳ **không** chứng minh thiết bị tin cậy gói đó.
- Không mở quyền tùy ý `os`, `io`, `package`, `debug`, `loadfile`, `dofile`, `require` trong Lua beta. Giữ hạn mức hiện hành (source, heap, instruction, deadline, draw calls). Thay đổi hạn mức phải có benchmark, kiểm thử ác ý và ghi rõ phiên bản hỗ trợ.
- Giữ giao diện OS Retro-Go như bản trước khi cập nhật lõi Back; những popup Back phải tái dùng widget thông báo sẵn có, không sửa theme/asset/renderer nếu không được yêu cầu.
- IDE thao tác trong workspace allow-list; không bỏ chặn `../`, symlink escape, tệp nhị phân và concurrent edits; không sửa file người dùng khi kiểm tra GUI offscreen.
- Update dependency **staging → pip check → GUI probe thật → active-runtime switch**; rollback phải hoạt động khi thất bại. Không tự nâng cấp gói hệ thống hay xóa `.venv`/dự án để 'sửa nhanh'.

## 5. Quy trình thực thi của từng tác vụ

**PLAN:** mô tả hành vi hiện tại, kết quả cần đạt, tệp được phép sửa, lựa chọn thay đổi tối thiểu, cách quay lại, môi trường có/không có.

**IMPLEMENT:** chia thay đổi thành patch nhỏ theo module; tạo bài test trước/sau nếu là lỗi; tránh tự ý đổi format/ABI/visual. Với tính năng chưa có runtime, dùng ADR và feature flag; không làm menu giả chưa hoạt động.

**VERIFY:** chọn đúng skill trong `SKILLS.md`, chạy test có thật, ghi nguyên lệnh + exit code + môi trường. Đối với GUI: Qt offscreen thực tế nếu có PySide6; không xem mockup PNG là screenshot GUI. Đối với firmware: build PlatformIO chưa tương đương chạy board, Serial 115200 + LCD video cần xác nhận riêng.

**REPORT:** nộp `summary`, `changed_files`, `tested`, `skipped`, `known_issues`, `compatibility`, `screenshots/logs`, `rollback`. Áp dụng mẫu `docs/agents/HANDOFF_TEMPLATE.md`. Nếu chưa được phép push, chỉ xuất patch/ZIP; không tuyên bố đã commit/push.

## 6. Các lỗi cần chủ động tìm

- `Back` trong app/game không được reset OS; `No` quay lại game **cùng trạng thái**, `Yes` dọn dẹp rồi về launcher, không chồng popup, âm thanh/đồng hồ không ghi đè lên dialog.
- Cài app/themes phải có rollback khi package sai hoặc mất nguồn, không xuất hiện bootloop; phân biệt build/host test với đo thiết bị thực.
- GUI sau cập nhật không khởi động, thiếu Qt platform plugin, tệp package sai venv, không mở Explorer/editor/VM hoặc pipeline log làm lộ key.
- Đồ họa không lệch màu RGB565, clipping ở mép màn hình và không làm giảm FPS ngoài ngân sách có kiểm chứng.

## 7. Quy tắc hợp tác nhiều Agent

Agent điều phối giao việc qua `agents/README.md`; một agent sở hữu một phần thay đổi tại một thời điểm. Khi hai nhiệm vụ đụng `studio/gui/window.py`, `tools/qstudio.py`, hoặc `src/main.cpp`, tạo kế hoạch merge trước, không ghi đè diff của nhau. Reviewer phải so baseline/hash, chạy test và xác nhận bằng chứng. Dùng commit `docs:`, `feat:`, `fix:`, `test:`, `perf:` với phần mô tả thay đổi, test, rủi ro; không force-push trừ khi có chỉ dẫn rõ.

## 8. Định nghĩa hoàn thành

- Đường dẫn và lệnh khớp mã nguồn thật; không có đường giả/placeholder có vẻ hoạt động.
- Tất cả test liên quan đã chạy; PASS/FAIL/SKIPPED/NOT_RUN phân loại riêng, không đổi SKIP thành PASS.
- Nếu chỉ thay tài liệu: kiểm tra markdown/path và smoke CLI; **không** nhận vơ kết quả thiết bị.
- Nếu sửa firmware lõi: UI/asset cũ bất biến (trừ yêu cầu được duyệt), build và test Back, có hướng dẫn thu Serial 115200.
- Chỉ phát hành thiết bị sau khi có log ESP32-S3 và bằng chứng LCD/âm thanh/FPS tương ứng.
