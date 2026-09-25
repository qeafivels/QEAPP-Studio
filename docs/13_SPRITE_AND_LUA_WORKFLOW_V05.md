# QEAPP Studio v0.5 — Pixel Sprite / Lua / ESP32-S3 workflow

## Mục đích

Từ template hoặc ảnh PNG nhỏ, tác giả game có thể biên dịch **mask 1-bit** nhúng trong Lua, xem trước trò chơi qua **cùng mã C++ VM** trên PC, kiểm tra chữ ký `.qeapp`, rồi thử tải lên bản firmware **`vqeaf_lua_beta`** (sau khi tự biên dịch và nạp board).

Không nhầm ảnh PNG xem trước trên PC với ảnh ST7789, và không nhầm signed `type=lua` beta với định dạng game native trên firmware sản xuất. Firmware VQEAF OS v2.4.2 mặc định chỉ hỗ trợ `web/text`.

## Quy trình IDE (Windows)

1. `py -3 -m pip install -r requirements-studio.txt` (GUI PySide6 và Pillow ở **máy phát triển**).
2. `run_studio.bat` → **New Sprite Lua Game (Beta)** hoặc **New Lua App (Beta)**.
3. Double click file PNG trong Explorer để **xem trước pixel bằng nearest-neighbor**; PNG preview giới hạn 1 MiB/512×512, không cấp quyền sửa binary.
4. Mở `main.lua` và chọn **File → Insert Pixel Sprite PNG**. Chọn PNG 1..32 pixel mỗi chiều, tên biến; IDE chèn Lua string `\xHH` trực tiếp vào source. Sprite **không phải** file tải tự động từ SD.
5. Trong `on_draw`, gọi `engine.blit1(x,y,w,h,bits,rgb565)`. `0` là trong suốt; `1` lấy màu RGB565 được truyền. Đọc ví dụ `projects/lua-sprite/main.lua`.
6. Lưu bằng Ctrl+S; F6 **Validate** → F8 **Preview Lua on PC** (có input replay từng frame từ Gamepad). Xem kết quả render 240×320 giả lập và log.
7. Ký khi public key đã được thêm vào firmware beta: F7 hoặc CLI build dưới đây. Không dùng private key trong repo, log hoặc thẻ nhớ.
8. Chỉ khi real hardware test PASS mới thử chép gói vào `microSD/System/Apps/Inbox/`, cài qua App Installer.

CLI (thực thi từ thư mục root kit):

```powershell
py -3 tools/pixel_sprite.py projects/lua-sprite/assets/ship_16x16.png --name ship --mode alpha --color 0xFFE0 -o generated_ship.lua
py -3 tools/qstudio.py init --template lua-sprite --id demo_ship --name "Demo Ship" -o my-ship
py -3 tools/qstudio.py validate projects/lua-sprite
py -3 tools/bootstrap_lua.py                   # tải Lua 5.4.8 + kiểm SHA256
py -3 tools/build_lua_host.py
py -3 tools/lua_preview.py projects/lua-sprite/main.lua --frames 30 -o build/ship.png
```

Lệnh ký beta, yêu cầu key đã tự provision từ máy phát triển và public key **đúng với firmware được nạp**:

```powershell
py -3 tools/provision_lua_beta_key.py --private C:\SecureKeys\vqeaf-lua-beta-private.pem
py -3 tools/qstudio.py build projects/lua-sprite --experimental-lua --firmware-root firmware/VQEAF-OS --sign-key C:\SecureKeys\vqeaf-lua-beta-private.pem --key-id 0x544c5541 -o dist/ship.qeapp
pio run -d firmware/VQEAF-OS -e vqeaf_lua_beta
```

**Cảnh báo:** Nạp firmware beta thử nghiệm chỉ khi có backup; phần build/chạy ESP32-S3, PSRAM và SPI LCD cần chạy trên thiết bị thật, hiện không được chứng minh bởi các kiểm thử host.

## ABI `engine.blit1` beta

```lua
engine.blit1(x, y, width, height, packed_mask_binary, color_rgb565)
```

- Mask 1-bit **row-major MSB-first**, byte dài chính xác `(width*height+7)//8`, bit padding cuối phải bằng `0`.
- `1 ≤ width,height ≤ 32`; tọa độ game nằm trong 240×270 (29 dòng status + 21 dòng footer do hệ điều hành quản lý); clipping trước khi gửi lệnh vẽ.
- Bit 0 không vẽ đè pixel nền. Màu đúng 16-bit RGB565 (0..65535).
- Mỗi hàng gom run liên tiếp thành rectangle cao 1; preflight **toàn bộ** ngân sách 512 lệnh vẽ trước khi vẽ một phần sprite.
- Toàn bộ mask nhúng trong script đã ký; script không được mở file/SD/network trực tiếp; key OS luôn được lọc.
- Mặt hạn chế: sprite đơn sắc một màu mỗi lần gọi; không có atlas, alpha thật, scaling, xoay, tilemap. Bản kế tiếp sẽ đánh giá palette-RLE và vùng sprite 8×8/16×16 để giảm thời gian SPI.

## Cấu trúc mẫu

```text
projects/lua-sprite/
├── qeapp.project.json             # metadata máy phát triển (không ghi JSON thẳng vào QEAPP/2)
├── main.lua                       # app entry, chứa mask nhúng
├── assets/ship_16x16.png           # ảnh thiết kế; KHÔNG đưa trực tiếp vào target package
└── README.md
```

## Release gates

- `python tools/verify_v05.py --system-lua` dùng liblua5.4 hệ thống **chỉ để chẩn đoán Linux host** khi chưa bootstrap Lua chính thức.
- Chính thức: `python tools/bootstrap_lua.py` → `python tools/verify_v05.py --require-qt` (máy dev cài PySide6), sau đó kiểm thử PlatformIO + Serial 115200 + PSRAM/TFT/SD, rồi mới gắn nhãn device verified.
- Kiểm thử đầu cuối tối thiểu: tạo key beta, ký gói, kiểm key-id, cài trong beta, chạy sprite & replay nút, quay Home khi phím MENU, giả lập package signature sai phải từ chối, khởi động lại và kiểm memory drift.
