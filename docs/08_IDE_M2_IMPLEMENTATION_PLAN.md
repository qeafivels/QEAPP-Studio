# M2 — Kế hoạch triển khai QEAPP Studio GUI (CHƯA TRIỂN KHAI)

Bước tiếp theo dự kiến phát triển một GUI kiểu IDE có thể chỉnh sửa text/web có thật và chạy **host simulator** cho ví dụ C++ hiện có. Không trình bày giao diện này như sản phẩm đang tồn tại; v0.2 chỉ có CLI + core host.

## Thư mục dự kiến

```text
studio/
  main.py                       # PySide6 bootstrap + settings window
  project_explorer.py           # giới hạn sandbox theo project root
  editors/{text,code}.py        # UTF-8 editor, validation errors
  widgets/{assets,build_log}.py # preview PNG/RGB565 / structured logs
  services/{project,commands}.py# duy nhất gọi qstudio CLI
  simulator/{panel,worker}.py   # preview PNG / Build Stop / worker process
  devices/serial_monitor.py     # chỉ đọc log, không tự flash
  tests/test_gui_offscreen.py
```

## Luồng người dùng và exit gate

1. **New Project**: hiện chỉ `text` và `web` export signed QEAPP/2; `native-host` là ví dụ **simulator only**. Mọi lựa chọn hiện rõ nhãn tương thích.
2. **Explorer / Editor**: điều hướng bên trong project root, không chép private key vào workspace. Khi Save phải backup hoặc ghi an toàn tránh file bị cắt khi IDE crash.
3. **Build**: GUI gọi CLI gốc `tools/qstudio.py validate/build/inspect`, hiển thị stdout và trạng thái; signing key từ user chọn ở phiên build, không lưu history, ẩn path và stderr có chứa thông tin nhạy cảm.
4. **Preview**: worker gọi `qstudio.py simulate`, xem ảnh output 240x320 và báo host-only. Chỉ khi game engine host thật được mở rộng thì mới hỗ trợ input tương tác qua IPC; v0.2 hiện là replay định sẵn.
5. **Stop**: terminate và wait subprocess worker; fallback kill process tree khi buộc dừng; không để PID lạc hay khóa file build.
6. **Project build matrix**: `text`/`web` → QEAPP/2 hợp lệ nếu signer và đúng trust-key. `native-host` → PNG host. `lua-proposal` → NOT_IMPLEMENTED. Chưa có một project nào cho Lua phát hành ra game độc lập.
7. **Release gate M2**: offscreen PySide6 tests, test cancel giữa compile, invalid path, missing compiler, tamper signature, CI screenshot hash, optional serial monitor smoke có thiết bị thật.

### Hướng dài hạn

M3 duyệt `ADR-QEAPP3.md` gồm header/manifest/engine ABI asset index/signer capability trước khi viết M4 Lua sandbox. IDE cần phân biệt rõ phiên bản firmware và runtime tối thiểu của project, không tự tạo QEAPP/3 chưa được phê chuẩn.
