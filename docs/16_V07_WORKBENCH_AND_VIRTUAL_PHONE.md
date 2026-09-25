# QEAPP Studio 0.7 — Developer Workbench & Virtual Phone

## Phạm vi

**v0.7.0 PC host candidate** nâng cấp dựa trên toàn bộ source v0.6, không chép mã nguồn, biểu tượng hay hình ảnh giao diện từ LuaS30-IDE. Bố cục và luồng làm việc tham khảo các khái niệm IDE thông dụng: activity rail, Explorer/Search, editor tabs, Output/Problems và virtual phone bên phải. **KHÔNG** phải giả lập CPU ESP32-S3 hoặc hệ điều hành VQEAF đầy đủ. PC VM chạy Lua 5.4 bằng `QeLuaRuntime.cpp` dùng chung với firmware beta. Phần hiển thị đồ họa máy ảo là khung Lua host 240×270 RGB565 cộng 29px top/21px bottom (240×320).

## Các tính năng nâng cấp

1. **GUI**: sửa thiếu import `QFrame` trước đây khiến constructor GUI lỗi ngay khi chạy Qt; đổi menu File/Edit/View/Run; tinh chỉnh thanh công cụ hiển thị chữ không cần emoji/icon font; bố cục tìm kiếm riêng trong thanh trái; Problems riêng dưới editor, giữ tab Output và lưu kích thước các splitter.
2. **Search**: `Ctrl+Shift+F` tìm kiếm literal toàn bộ mã nguồn (bao gồm buffer chưa lưu). Giới hạn truy cập theo `Workspace`: tối đa 500 tệp UTF-8, 8 MiB tổng đọc, 250 kết quả; không theo symlink, không đọc PEM/private key, build/dist, PNG hay thư mục ẩn. Double-click kết quả chuyển đúng tệp/dòng/cột mà không ghi đè nội dung ngoài disk.
3. **Editor**: gutter số dòng và dòng hiện tại, Ctrl+F Find, Ctrl+H Replace, Ctrl+G Go to Line, thanh trạng thái dòng/cột; giữ lưu atomically và cảnh báo khi file đã đổi bên ngoài.
4. **Máy ảo**: Pause/Resume, Step một frame, chọn trần timer host 15/30 FPS; backpressure luôn chỉ tối đa 1 frame đang đợi, watchdog 5 giây, giữ nút bàn phím rồi thả khi chuyển focus. Chặn các phím hệ thống không hỗ trợ như v0.6; MENU/A/B chỉ đóng guest, SELECT đổi trạng thái host và **chưa** giả lập T9.
5. **Chỉ số thực của PC**: hiển thị FPS số frame giao tới UI theo cửa sổ 1 giây, đồng hồ thanh trạng thái lấy giờ PC thật, round-trip response ms, thời gian `update+render` guest trung bình/30 frame từ host, heap hiện tại/peak của Lua VM. Chỉ số này **không phải** ESP32-S3 FPS, SPI, PSRAM hoặc thời gian truyền LCD.
6. **CLI/headless**: `virtual_phone_cli.py --frames 30` trả JSON gồm host-throughput, heap, render_us và PNG lấy từ framebuffer thực; `tools/verify_v07.py` chạy compileall, VM C++17 build, Studio tests, legacy host tests và CLI 30 frame; chạy Qt offscreen chỉ khi PySide6 có sẵn. Báo cáo phân biệt SKIPPED/NOT RUN với PASS.

## Luồng dành cho lập trình viên trên Windows

```powershell
cd QEAPP-Studio-v0.7
py -3 -m pip install -r requirements-studio.txt
py -3 tools/bootstrap_lua.py
py -3 tools/verify_v07.py --require-qt
py -3 run_studio.py
```

Nếu không có Internet, có thể dùng archive Lua 5.4.8 tải từ nguồn chính thức đã kiểm tra SHA-256, qua `tools/bootstrap_lua.py --archive C:\Downloads\lua-5.4.8.tar.gz`. Trên Linux đã có `liblua5.4.so.0`: `python tools/verify_v07.py --system-lua` chỉ là chẩn đoán **PC**, không dùng fallback đó để xác nhận firmware.

Trong Studio: **New Lua App (Beta)** hoặc Open Project → mở `main.lua` → Ctrl+S → F6 Validate → F9 Run VM → Pause/Step/30 FPS → lưu ảnh PNG. F8 replay có đầu vào được lưu ở `tests/input_replay.json`. F7 gọi firmware packer có ký P-256, **không** lưu đường dẫn private key trong preferences. Đối với package đã ký, Inspect SHA-256 và xác minh P-256 với public PEM phù hợp trước khi chép vào microSD; kiểm tra trust-anchor thật trên firmware vẫn bắt buộc.

## Ma trận thực thi thực tế

| Phần | PC virtual phone v0.7 | ESP32-S3 / VQEAF |
|---|---|---|
| Game Lua source `.lua` | Có: Lua 5.4 C++ host VM giới hạn | Chỉ `vqeaf_lua_beta` sau khi ký đúng publisher; phần cứng chưa kiểm tra trong bản này |
| 240×320, D-pad/screenshot | Có: 270px Lua game + 50px PC chrome | Cần test GPIO/TFT thật và serial benchmark |
| Text/web `.qeapp` | Build/Inspect; host C++ demo riêng | Stock firmware hỗ trợ signed text/web theo contract QEAPP/2 |
| Theme, SD, Wifi, browser, launcher/installer | Không mô phỏng | Chỉ firmware thật; **không khẳng định** host kiểm thử install/reset |
| FPS/ms/heap tại virtual phone | Chỉ là PC host | Cần lấy từ Serial 115200 trên board thật |
| `menu/back/select/T9` trong guest Lua | menu/back = host stop; SELECT indicator | Không giả định map firmware input khi chưa test board |

## Ghi chú bảo mật

- Bảo lưu QEAPP/2, xác minh chữ ký ECDSA P-256, signer firmware và chế độ beta riêng, không cấp đặc quyền cho file project không tin cậy.
- VM desktop không cấp API tùy tiện tới network, filesystem, shell hoặc SD. `QProcess` chỉ chạy executable `qe_lua_host` do builder tin cậy tạo; guest chỉ gửi event tên phím thuộc allow-list.
- Không đóng gói bất kỳ private key, binary host đã biên dịch, ảnh mô phỏng không xác thực hoặc asset của LuaS30-IDE.
- Test PySide6 offscreen chưa thực thi trong Linux environment do thiếu Qt. **Không được phát hành desktop GUI là `GUI_VERIFIED`** cho đến khi hoàn thành trên Windows. Chưa có build PlatformIO và kiểm thử board thật trong phiên này.
