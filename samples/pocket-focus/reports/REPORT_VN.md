# Pocket Focus — Kết quả kiểm thử mẫu

- Môi trường: bộ mã nguồn QEAPP-Studio v0.7.4; Linux + system liblua5.4 (chẩn đoán PC).
- Số kiểm tra: **13 / 13 PASS**
- Project validation: `pocket-focus-lua` và `pocket-focus-guide` hợp lệ.
- 7 kịch bản giao diện: ảnh PNG thực xuất bởi C++ Lua host VM.
- Hai luồng thời gian rút ngắn: Work -> Break; Auto-break Off -> Complete: PASS.
- ECDSA P-256 ký/kiểm tra host: guide text + Lua beta: PASS với khóa tạm KHÔNG đóng gói.
- Trên thiết bị ESP32-S3: CHƯA KIỂM THỬ; Windows PySide6 GUI: CHƯA KIỂM THỬ.
- Không kiểm tra âm thanh vì VM hiện không có Lua audio bridge.

## Danh sách kiểm thử
- VALID project pocket-focus-lua
- VALID project pocket-focus-guide
- REAL HOST LUA home
- REAL HOST LUA running
- REAL HOST LUA paused
- REAL HOST LUA settings
- REAL HOST LUA stats
- REAL HOST LUA end_dialog
- REAL HOST LUA resume
- WORK -> BREAK timed phase transition
- AUTO BREAK OFF -> completion
- guide host signed package + verify supplied temporary public key
- lua-beta host signed package + verify supplied temporary public key

## Bằng chứng
- `screenshots/00_OVERALL_REAL_HOST_PREVIEW.png`: 6 trạng thái UI từ VM thật, không phải ảnh chụp LCD ESP32-S3.
- `reports/host_verification.json`: dữ liệu kiểm tra, SHA-256 từng PNG.
- `tests/verify_sample.py`: tái chạy để đối chiếu.

### Kiểm thử hiện hành chưa có
- Nạp firmware beta và chạy app Lua trên ESP32-S3 thực.
- Cài pocket-guide trên VQEAF stock với khóa publisher đã ghim và thẻ microSD.
- Kiểm thử sleep, watchdog, FPS LCD và âm thanh (không có audio API guest).
