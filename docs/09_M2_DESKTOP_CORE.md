# QEAPP Studio v0.3 — M2: Desktop IDE core + GUI

Phiên bản: **M2 alpha**. Đích: PC Windows (PySide6, Python 3). Một phần core chỉ dùng Python stdlib nên có thể tự kiểm thử trên Linux/macOS. Engine C++17 M1 kế thừa v0.2 và **chỉ chạy host simulator**.

## 1. Cấu trúc mới

```text
QEAPP-Studio/
  run_studio.py, run_studio.bat      # launcher desktop
  requirements-studio.txt           # PySide6; cryptography; Pillow
  studio/
    main.py                          # Qt app bootstrap, báo thiếu PySide6
    core/
      workspace.py                   # sandbox project filesystem, atomic save
      config.py                      # cài đặt người dùng, KHÔNG lưu private key
      commands.py                    # argv typed của tools/qstudio.py
      jobs.py                        # stream, cancel, timeout, process tree, log redaction
    gui/
      window.py                      # PySide6 editor/explorer/preview/log/actions
    tests/
      test_core.py                   # chạy không cần Qt
      test_gui_offscreen.py          # chạy khi cài PySide6; nếu không SKIPPED
  engine/                            # M1 C++17 host runtime giữ nguyên
  examples/                          # Snake, Hello host-only
  projects/                          # text/web có thể ký; Lua prototype chưa chạy
  tools/qstudio.py                   # builder/inspector/CLI chuẩn từ v0.2
  docs/01..08                         # hợp đồng QEAPP2, engine, workflow
  docs/09_M2_DESKTOP_CORE.md
```

## 2. Trình tự tạo và phát hành ứng dụng `.qeapp`

1. `run_studio.bat` hoặc `python run_studio.py`. Chọn **New Text App** hoặc **New Web App**; **không có lựa chọn giả tạo Build Lua**.
2. Explorer hiển thị source bên trong project; editor UTF-8, tab có dấu `●` khi chưa Save. `Ctrl+S` ghi atomically; không ghi đè nếu file bị thay đổi từ ngoài.
3. **Validate (F6)** bắt buộc trước release. Web phải HTTPS, text phải có payload 1..262144 byte, icon tùy chọn PNG 32×32. Bộ kiểm tra và packer là script gốc từ firmware (`tools/qstudio.py` gọi `tools/build_qeapp.py`).
4. Chọn **Firmware Source** (đường dẫn checkout VQEAF OS hiện hành, có `tools/build_qeapp.py`). **Build (F7)** yêu cầu chỉ định PEM private key mỗi lần, không lưu vào history/config. Chọn key-id phải khớp public key ghim trên firmware.
5. Bản `.qeapp` nằm tại `<project>/dist/<id>.qeapp` (không commit private key). **Inspect** kiểm tra cấu trúc+hash; chọn public PEM nếu cần kiểm tra chữ ký. Đối chiếu với trust anchor firmware trên thiết bị riêng, không coi chữ ký hợp lệ với *bất cứ* public PEM là đủ điều kiện cài đặt.
6. Sao chép `.qeapp` đã xác minh sang SD `System/Apps/Inbox/` và kiểm thử trên VQEAF OS; Studio v0.3 không tự động flash/cài.

## 3. Workflow cho game và preview

**Run Host Preview** chọn `Snake` hoặc `Hello` + scenario `ready/playing/paused`. Worker build C++17 và replay fixed frames trên PC → xuất PNG 240×320 trong `build/host_preview/`. Đây là test renderer/input/routine M1, KHÔNG đóng gói native/Lua thành QEAPP/2. Tham khảo `docs/07_M1_HOST_ENGINE.md` và draft ABI ở `docs/04_API_DRAFT.md`.

Muốn game `.qeapp` cài được tùy ý: cần chốt ADR package version mới, port runtime với quản lý memory/capabilities lên ESP32-S3, viết loader/parser/verifier, sandbox watchdog và kiểm thử thực trên board. **Không** thay manifest QEAPP/2 từ `web/text` sang `lua/native` vì firmware hiện tại từ chối.

## 4. Bất biến bảo mật, độ ổn định

- `Workspace` giới hạn file UTF-8 <=1 MiB, extension allow-list, không mở/edit symlink, hidden, `dist/build`, `.git`, `.pem/.key`, chặn `..`; New Folder dùng quy tắc tương tự.
- Atomic save bằng tempfile + `fsync` + `os.replace`; so hash trước ghi, báo conflict nếu tệp đổi. Không cam kết atomic cross-process filesystem locking.
- Preferences đặt tại `%APPDATA%/QEAPPStudio/settings.json` trên Windows, hoặc `~/.config/QEAPPStudio/settings.json`; chỉ chứa recent paths và firmware root. Signing PEM **không** lưu.
- CLI nhận argv list, không `shell=True`. Job log loại bỏ private key path; chặn job đồng thời, timeout, stop cả process tree (`taskkill /T /F` Windows, `killpg` POSIX).
- Qt worker chạy QThread, thông báo về main thread bằng Signals, screenshot chỉ hiển thị sau job code=0. Muốn thử GUI offscreen cần cài PySide6.
- Editor Explorer cố ý không hiển thị binary asset ở v0.3; icon PNG 32×32 được tham chiếu qua JSON và xác thực bằng validate. Trình duyệt asset hình trong IDE là milestone tiếp.

## 5. Phân biệt mức kiểm thử

| Gate | Nội dung | Cần môi trường |
|---|---|---|
| Host Core | project FS, path escape/symlink, atomic write, cancel/timeout, log redaction | Python stdlib |
| Qt GUI | tạo window, open source tab, kiểm tra nút Stop | PySide6 + offscreen |
| QEAPP/2 signer | ký bằng khóa temporary P-256, verify/tamper, build text/web | Firmware source + cryptography + Pillow nếu có icon |
| Host renderer | PNG 240x320 + SHA golden + replay 1200 tick | g++/clang++ |
| ESP32 | build firmware, ký đúng trust key, install/update/reboot, theme/browser, watchdog | Board thật + PlatformIO |

Không được ghi PASS cho gate Qt/ESP32 nếu môi trường chưa chạy được.

## 6. Mốc phát triển tiếp

M2.1: asset preview/import/sprite atlas có giới hạn RGB565, search code, undo/redo, test GUI đa nền tảng; M3: ADR QEAPP/3 + signed asset-index; M4: Lua/scripting runtime host có budget, M5: port lên ESP32-S3 và làm E2E cài game độc lập (chỉ khi gate chứng minh).
