# SKILLS.md — QEAPP-Studio Agent Execution Skills

> **Baseline mã nguồn: QEAPP-Studio v0.7.4.** Đây là các playbook theo trigger để AI Agent thực thi công việc và báo cáo kết quả có bằng chứng. Đọc `PROMPT.md` trước. Lệnh dùng `python` theo hệ điều hành; trên Windows đã cài Python 3, có thể dùng `py -3` hoặc interpreter active từ launcher.

## Bảng kích hoạt nhanh

| Trigger | Skill | Agent chủ trì | Gate chính |
|---|---|---|---|
| 'new app/game', project JSON, template | S01 | `agents/app-template.md` | init + validate + preview (nếu Lua) |
| IDE/Editor/Explorer/theme desktop | S02 | `agents/studio-gui.md` | GUI offscreen thực + Studio tests |
| Lua VM, input, fps host | S03 | `agents/lua-runtime.md` | bounded VM + replay + leak/crash |
| build, signer, install `.qeapp` | S04 | `agents/package-security.md` | validate + inspect signature + compatibility |
| firmware, Back, performance thiết bị | S05 | `agents/firmware-core.md` | host regressions + PlatformIO + Serial gate |
| launcher, dependency, repair, rollback | S06 | `agents/studio-gui.md` | launcher tests + Qt post-update + rollback |
| test/release/report | S07 | `agents/qa-release.md` | test matrix + evidence + diff audit |

## S01 — Tạo app/game mẫu

**Khi dùng:** tạo project mới. Chọn rõ loại `text`, `web` (stock) hoặc `lua` (beta). Không biến host preview thành khẳng định `.qeapp` Lua chạy trên stock OS.

```sh
python tools/qstudio.py init --template text --id demo_notes --name "Demo Notes" -o projects/demo-notes
python tools/qstudio.py init --template lua --id demo_lua --name "Demo Lua" -o projects/demo-lua
python tools/qstudio.py validate projects/demo-notes
python tools/qstudio.py validate projects/demo-lua
# chỉ khi đã bootstrap + build Lua host:
python tools/qstudio.py lua-preview projects/demo-lua --frames 14 -o build/demo-lua.png
```

Mẫu thực tế: `projects/lua-hello/`, `lua-snake/`, `lua-sprite/`, `text-notes/`, `web-bookmark/`. `qeapp.project.json` (PC metadata) chứa `project_format=1`, `id`, `name`, `version`, `type`, và `content` hoặc `url`; `icon` tùy chọn PNG 32×32. `id` `[a-z0-9_-]{1,24}`, `name` printable ASCII 1..40, `version` số dấu chấm ≤19 ký tự. Không đưa `build/`, `dist/` hoặc key vào template.

**Pass:** validate exit 0; preview chỉ PASS nếu PNG thực từ VM cùng log/replay; ký/cài là gate riêng.

## S02 — Desktop GUI và IDE

**Khi dùng:** PySide6, Explorer, editor, panels, virtual phone, diagnostics. Đọc `studio/gui/window.py`, `studio/gui/virtual_phone.py`, `studio/core/workspace.py`, `tools/gui_post_update_check.py`; giữ chức năng thật của mọi nút. Chỉ đổi UI **IDE** khi có yêu cầu; theme/renderer **firmware OS** là phạm vi khác.

```bat
run_studio.bat --diagnose
run_studio.bat --gui-check
run_studio.bat
```

Linux/macOS có PySide6: `QT_QPA_PLATFORM=offscreen python tools/gui_post_update_check.py --output build/gui-check.json --screenshot build/gui-check.png`. Chạy `python -m unittest discover -s studio/tests -v`. Không có PySide6: thông báo **GUI NOT_RUN/SKIPPED**, vẫn có thể chạy core tests. Ảnh do `make_ui_mockup.py` là ảnh minh họa, không phải bằng chứng Qt thật.

**Pass:** GUI khởi tạo `QApplication/StudioWindow`, mở tệp dự án tạm, editor/Explorer/virtual device hoạt động, ảnh offscreen có thật và không sửa project người dùng. Windows Qt platform plugin phải kiểm chứng riêng trên Windows.

## S03 — Lua host VM và preview

**Khi dùng:** Lua callbacks, RGB565, timeout, FPS, crash, replay. Đọc `docs/10_LUA_BETA_ARCHITECTURE.md`, `runtime/`, `studio/core/frame_protocol.py`. **Lua host** dùng cùng nguồn core C++ nhưng không giả lập microSD/installer/I2S/CPU ESP32.

```sh
python tools/bootstrap_lua.py
python tools/build_lua_host.py
python tools/qstudio.py lua-preview projects/lua-snake --frames 14 --replay tests/input_replay.json -o build/lua-snake-test.png
python tools/test_lua_beta_host.py
python -m unittest discover -s tests -v
```

Trên Linux, `python tools/build_lua_host.py --system-lua` chỉ dùng khi có `liblua5.4` và **chỉ là chẩn đoán host**, không đủ điều kiện build firmware. Đo `frame_count`, render/VM ms, heap, watchdog, input lag với môi trường/hệ số chuẩn. Đối chiếu ảnh bằng CRC/hash nếu có baseline và kiểm tra trực quan khi golden thay đổi.

Giữ callbacks `on_update(dt)`, `on_draw()`, `on_key(key,down)`. Lua API hiện có `engine.clear`, `rect`, `text` và `blit1` (nếu version core hỗ trợ). `engine.width=240`, `engine.height=270` thuộc vùng vẽ dưới status/footer trong runtime beta hiện hành; LCD tổng thể vẫn 240×320. Không tự suy ra API `audio.play`, `filesystem`, `wifi` chưa được triển khai.

**Pass:** suite liên quan thành công; đánh dấu rõ lỗi thiếu Lua source/toolchain và `SKIPPED` không thay `PASS`.

## S04 — Signed QEAPP/2 + firmware compatibility

**Khi dùng:** build/export/install/rollback/signature. Đọc *parser và signer thực* trong firmware target trước khi đóng gói. Stock hỗ trợ `text|web`; Lua chỉ build khi chủ động chọn beta + key beta tương ứng.

```sh
python tools/qstudio.py validate projects/text-notes
python tools/qstudio.py doctor --firmware-root ../VQEAF-OS
# chỉ dùng key riêng của người phát hành được lưu bên ngoài repo:
python tools/qstudio.py build projects/text-notes --firmware-root ../VQEAF-OS --sign-key <PRIVATE_KEY_PATH> -o dist/text-notes.qeapp
python tools/qstudio.py inspect dist/text-notes.qeapp --public-key <TRUSTED_PUBLIC_KEY_PATH> --key-id <MATCHING_KEY_ID>
```

`--experimental-lua` chỉ dành cho `vqeaf_lua_beta` và riêng `tools/provision_lua_beta_key.py`. Không dùng gói text/web ký production để giả định tương thích beta key khác. Inspect bằng PEM được chỉ định **chưa** xác minh public key đã ghim trên thiết bị. Khi người dùng yêu cầu app chạy stock, dùng `text/web`, không chọn Lua chỉ vì preview thành công.

**Pass:** package hợp lệ theo parser, signature đúng key dự kiến, tamper bị từ chối, key-id trùng trust firmware, hành vi cài/update được xác minh ở tier thích hợp. Không đưa private key vào patch hay screenshot.

## S05 — Firmware lõi, Back và thiết bị thật

**Khi dùng:** input router, dialogs, installer, theme safety, FPS/đồ họa/âm thanh game. Đọc checkout VQEAF OS người dùng chỉ định. ZIP Studio v0.7.4 **không phải** bằng chứng chứa firmware v2.5.1 Back r2 mới nhất. Không overwrite `src/main.cpp` từ baseline cũ.

**Bảo vệ đồ họa cũ:** snapshot SHA-256 tất cả file theme/icon/renderer trước và sau; các yêu cầu 'chỉ sửa lõi' phải giữ chúng nguyên byte. `A=Back` ở app mở OS confirm; `No` khôi phục session cũ, `Yes` dọn trạng thái trở về launcher; MENU=Home theo hợp đồng repo; không biến B=Delete thành Back. Không giả định guest nhận phím A.

```sh
pio run -d ../VQEAF-OS -e vqeaf_os
# chỉ chạy nếu đã provision beta + Lua source chuẩn:
pio run -d ../VQEAF-OS -e vqeaf_lua_beta
```

Lệnh PlatformIO chỉ là **build gate**. Thiết bị thật phải nạp đúng environment/board, chụp LCD, thu Serial **115200**, ghi reset reason, heap/PSRAM trước-sau cài, thử Back No/Yes ≥20 chu kỳ, đo FPS thực khi game chạy, quan sát âm thanh loa nếu game có SFX. Các chỉ số từ host không được ghi là FPS ESP32 hoặc audio phát qua loa. Thiết bị không kết nối → `DEVICE_NOT_RUN`.

**Pass:** không bootloop/crash, không rò memory qua lặp lại, Back callback đúng, display/âm thanh được kiểm chứng bằng log/video tương ứng.

## S06 — Windows launcher Safe Update & Repair

**Khi dùng:** lỗi `run_studio.bat`, thay Python dependency, venv hỏng, GUI không mở. Giữ `logs/active-runtime.json` rollback pointer, venv stage riêng và GUI probe thực; không nâng cấp trực tiếp env khỏe mạnh, không tự xóa project hoặc reset config chưa sao lưu.

```bat
run_studio.bat --diagnose
run_studio.bat --gui-check
run_studio.bat --update-now
run_studio.bat --rollback-update
run_studio.bat --offline
```

Sau cập nhật, kiểm `logs/launcher.log`, `logs/gui-check-active.json`, ảnh `logs/gui-check*.png`, `pip check`, explorer/editor/VM. Lỗi Qt → rollback có log và verify env cũ; không coi image sinh thủ công là GUI screenshot. Đọc `docs/17_SAFE_GUI_UPDATES_v074.md` để kiểm tra từng nhánh.

**Pass:** đã chạy pytest/unittest liên quan và thực thi GUI probe khi có Qt; trên môi trường không có Qt/Windows phải báo chưa xác minh thay vì PASS giả.

## S07 — QA, security và release

**Khi dùng:** tổng hợp, commit, release, báo cáo. Đi theo `docs/agents/TEST_MATRIX.md` và `docs/agents/HANDOFF_TEMPLATE.md`. Có ít nhất test cụ thể cho logic/CLI/VM/GUI/firmware liên quan, và test negative cho sandbox + package tamper khi sửa path/packer.

```sh
python tools/validate_agent_docs.py
python -m unittest discover -s studio/tests -v
python -m unittest discover -s tests -v
python tools/verify_v072.py --full      # môi trường đủ Lua toolchain; tùy bài test
```

`--require-qt` sử dụng khi muốn gate fail nếu Qt không chạy. Luôn ghi 4 trạng thái `PASS`, `FAIL`, `SKIPPED`, `NOT_RUN`, mức xác minh `STATIC | HOST | GUI_QT | PIO_BUILD | DEVICE`. Trước commit: `git diff --check`, kiểm không có `.pem/.key`, nhắc ảnh và hash nếu graphics gate. Cung cấp commit title + phần body nêu *why, what, tests, limitations* và chỉ báo push khi có log từ git.
