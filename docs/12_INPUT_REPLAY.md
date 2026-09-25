# Reproducible Lua gamepad replay (v0.4.1)

Mục tiêu: sửa lỗi điều khiển game trên PC bằng input **xác định**, phát lại qua cùng `QeLuaRuntime::key()` trước khi thử trên firmware. Bộ ghi UI không ghi âm hoặc kết nối điện thoại.

## Giao diện

Mở Lua project → panel **GAMEPAD REPLAY** ở bên phải → chọn tổng frame `1..200`, frame event `0..frames-1`, key `start/up/down/left/right/option`, trạng thái Press/Release → `+ Event` → Save Replay JSON → **F8**. `Undo event` xóa record mới nhất. F8 tự lưu recorder đang thay đổi; editor tab JSON mở sẵn được cập nhật khi ghi. Ảnh kết quả từ host không phải ảnh thiết bị.

Ví dụ file `projects/lua-snake/tests/input_replay.json`:

```json
[
  {"frame": 1, "key": "start", "down": true},
  {"frame": 2, "key": "start", "down": false},
  {"frame": 3, "key": "right", "down": true},
  {"frame": 4, "key": "right", "down": false}
]
```

Các giới hạn được áp dụng ở **cả Python và host runner C++**: 1..128 event, tối đa 8192 bytes JSON, key whitelist, frame hợp lệ, bool thật cho `down`, thứ tự press/release trong cùng frame được giữ nguyên sau sort. Không cho phép `MENU`, `A`, `B`, `SELECT`, symlink/path traversal qua project-relative CLI.

CLI tương đương:

```powershell
py -3 tools/qstudio.py lua-preview projects/lua-snake --frames 8 --replay tests/input_replay.json -o build/replay.png
```

`--replay` là đường dẫn **tương đối bên trong project** ở qstudio CLI. Chạy host theo tốc độ cố định để so sánh ảnh, không coi host timestamps là đo hiệu năng thiết bị. `tests/test_lua_v041.py` và `studio/tests/test_replays.py` kiểm tra giới hạn, màu/clipping, injection phím hệ thống, sort xác định và sandbox filesystem.
