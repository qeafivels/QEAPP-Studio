# Cấu trúc QEAPP-Studio v0.7.4 (đọc trực tiếp từ source ZIP)

Gói Studio đã đối chiếu: `QEAPP_Studio_v0.7.4_Safe_GUI_Update_Full_Source.zip`.
Sơ đồ rút gọn dưới đây trình bày các thư mục dùng cho lập trình ứng dụng; trong gói thực còn có firmware, test, tư liệu và file tài nguyên.

```text
QEAPP-Studio-v0.7.4/
├── run_studio.bat             # Khởi chạy Windows, kiểm tra môi trường, cập nhật an toàn
├── run_studio.py              # Khởi chạy Qt Python
├── requirements-studio.txt   # PySide6, cryptography, Pillow
├── studio/
│   ├── main.py               # Bootstrap IDE
│   ├── gui/
│   │   ├── window.py         # Giao diện làm việc chính
│   │   ├── code_editor.py    # Trình biên tập mã nguồn
│   │   ├── virtual_phone.py  # Máy ảo và phím điều khiển
│   │   └── theme.py          # Giao diện IDE
│   ├── core/
│   │   ├── workspace.py      # Truy cập project an toàn
│   │   ├── jobs.py           # Process/Stop/log
│   │   ├── config.py         # Thiết lập
│   │   ├── replays.py        # Tái hiện chuỗi phím có giới hạn
│   │   ├── diagnostics.py    # Chẩn đoán GUI
│   │   └── repair.py         # Sửa chữa môi trường
│   └── tests/
├── runtime/
│   ├── include/              # C++ runtime interface
│   ├── src/QeLuaRuntime.cpp  # Lua engine dùng cho host
│   └── host/qe_lua_host.cpp  # Lua guest PC runner
├── tools/
│   ├── qstudio.py            # Validate/build/inspect dự án QEAPP
│   ├── lua_preview.py        # Chạy guest Lua và ghi PNG 240x320
│   ├── build_lua_host.py     # Biên dịch máy ảo host
│   ├── virtual_phone_cli.py  # Điều khiển và đo máy ảo không cần Qt
│   └── safe_runtime_update.py
├── projects/                 # Dự án mẫu đi kèm
│   ├── lua-hello/
│   ├── lua-snake/
│   ├── lua-sprite/
│   ├── text-notes/
│   └── web-bookmark/
├── firmware/VQEAF-OS/        # Firmware tham chiếu / bộ đóng gói có ký
├── docs/                     # Hợp đồng ABI, cảnh báo và hướng dẫn
└── tests/                    # Kiểm thử host
```

## Quy trình dùng Studio

1. Mở `run_studio.bat` trên Windows để chuẩn bị môi trường và mở IDE.
2. File > Open Project chọn `projects/pocket-calculator-lua` của bộ mẫu này.
3. Mở `main.lua` trong Editor. `F6` để Validate; `F9` để mở máy ảo Lua host. Tùy bản build Qt, dùng menu Run tương ứng.
4. `tools/lua_preview.py` là đường chạy headless đã kiểm thử, tạo PNG **thực từ framebuffer host**.
5. `qstudio.py build` chỉ chấp nhận Lua với `--experimental-lua` và firmware `vqeaf_lua_beta` đã cấu hình khóa công khai đúng.

## Quan trọng

- Máy ảo PC không phải bộ giả lập ESP32-S3; tốc độ hiển thị trong PC không đại diện TFT/SPI.
- Firmware stock hỗ trợ QEAPP/2 **text/web** có chữ ký. Dự án `pocket-calculator-guide` là ứng dụng đọc hướng dẫn tương thích loại này, không phải game/máy tính tương tác.
- Ứng dụng Lua tương tác chỉ chạy firmware **beta có Lua** khi đã cấu hình trust-anchor và xác nhận thử nghiệm trên board.
- Demo không sửa firmware, renderer, theme, OS Back dialog hay icon của hệ điều hành hiện tại.
