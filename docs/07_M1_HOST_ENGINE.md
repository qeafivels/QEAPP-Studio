# M1 — QEAPP Studio portable host engine (implemented in v0.2)

**Tình trạng:** Đã triển khai / chạy kiểm thử **trên PC**. CHƯA tích hợp firmware ESP32-S3 và **KHÔNG** biên dịch trò chơi/app C++ hoặc Lua thành `.qeapp` chạy độc lập.

## Thiết kế

```text
       qstudio.py simulate --demo snake|hello
                      |
               simulate_host.py
             (g++/clang++ C++17)
                      |
    +------------------------------------------+
    | engine/include/qe/runtime.h              |
    |  App interface, KeyEvent, Runtime         |
    |  fixed timestep, queue 32 events          |
    |  draw RGB565 clipped commands             |
    +------------------------------------------+
                      | Platform abstract
                  HostCanvas
                   RGB565 RAM
                      |
                 P6 PPM RGB888
                      |
                stdlib zlib PNG
                      |
               240x320 screenshot
```

`Runtime`, `App`, `PixelSink` và `Platform` là **interface thiết kế trong Studio**. Không thêm các header này vào VQEAF OS và chưa có phiên bản ABI công bố cho `.qeapp`. Giao diện tương lai trên board có thể dùng phương án draw theo tile hoặc bộ đệm PSRAM thay vì framebuffer đầy đủ.

### Các thành phần

- `engine/include/qe/runtime.h`: hợp đồng core, events, memory-budget hữu hạn; `Platform::reservedSystemKey` luôn giữ `MENU/Home`, `SELECT long-press` cho OS.
- `engine/src/runtime.cpp`: `init → onKey → fixed update → draw → pause/resume → shutdown`. `fixed_step_ms` mặc định 50 (20 tick/s); tối đa 4 bước bắt kịp cho mỗi `tick`. Thời gian dư vượt quota được đếm trong `dropped_ms`, không thực hiện hàng nghìn update sau lag.
- `engine/src/draw.cpp`: vùng chữ nhật có clipping, viền, sprite RGB565 trong giới hạn 256x256 và font 3x5 tối giản. Kiểm độ dài nguồn sprite trước khi đọc.
- `engine/host/HostCanvas.*`: framebuffer HOST 240x320x2 byte = **153.600 byte** do `std::vector` cấp phát khi khởi tạo; không phải mức SRAM do firmware sử dụng.
- `examples/snake_native_host`: game C++ dùng core mới, 16x18 ô, D-pad và OK; màn ready/play/pause; tính điểm và food RNG xác định trên PC.
- `examples/hello_native_host`: ví dụ ứng dụng tương tác; OK tăng đếm, OPTION đổi màu, BACK reset; dùng **cùng một core**.
- `tools/simulate_host.py`: biên dịch host, chạy demo, chuyển RGB888 PPM thành PNG không cần Pillow, xuất SHA-256 từng frame.
- `tests/test_engine.cpp` và `tests/test_host_engine.py`: C++ lifecycle/input/render + kiểm định screenshot và soak giả lập.

## Chạy ngay

Yêu cầu **Python 3.10+** và **g++/clang++ hỗ trợ C++17** trên PATH. Trên Windows cài bộ compiler riêng (VD. MSYS2/MinGW-w64 hoặc LLVM); không cần PlatformIO để chạy simulator PC.

```powershell
cd VQEAF_QEAPP_Studio_Developer_Kit_v0.2
py -3 tools/qstudio.py simulate --demo snake --scenario playing --frames 40 -o screenshots/snake.png
py -3 tools/qstudio.py simulate --demo snake --scenario paused  --frames 40 -o screenshots/snake_paused.png
py -3 tools/qstudio.py simulate --demo hello --scenario playing --frames 40 -o screenshots/hello.png
py -3 -m unittest discover -s tests -v
```

- `--frames` 0..2000, mỗi frame tương ứng 50 ms **mô phỏng thời gian game**, không chứng minh FPS thực trên ESP32.
- PNG đúng 240x320 và SHA-256 tính trên *file* lẫn framebuffer RGB888 xuất ra từ RGB565, vì vậy thay đổi một pixel sẽ tạo hash khác.
- `tests/golden/host_sha256.json` ghim hash cho 5 ảnh ready/playing/paused (Snake) và ready/playing (Hello). Đổi hash **chỉ sau khi chủ động xem lại ảnh và ghi lý do trong changelog**.

### Input & lifecycle

| VQEAF nút | M1 `qe::Key` | Hành vi |
|---|---|---|
| UP / DOWN / LEFT / RIGHT | Up / Down / Left / Right | Truyền tới app |
| START | Ok | Truyền tới app |
| A | Back | Truyền tới app theo policy chưa tích hợp |
| B | Delete | Truyền tới app |
| OPTION | Option | Truyền tới app |
| MENU | Menu | **Chặn**, gửi `Platform::reservedSystemKey` |
| SELECT giữ >600ms | SelectLong | **Chặn**, gửi callback OS |

Tại đây sự kiện `SelectLong` đã được chuẩn hóa sẵn; **phát hiện nhấn giữ 600ms từ GPIO là trách nhiệm của firmware**, không phải engine host. Chưa viết bộ thu sự kiện GPIO, chưa can thiệp vào keymap hoặc task hệ thống đang chạy.

### Bounded-memory và bảo vệ

- Engine core dùng ring buffer input **32 event** cố định và không cấp phát trong `Runtime::tick()`; khi đầy, drop event mới, tăng `input_overflows`. Hệ điều hành vẫn nhận reserved keys.
- Bộ renderer kiểm clipped rectangle, độ dài sprite và viewport, kiểm 50ms/frame step; host không xác minh DMA/ST7789 hay thời gian CPU ESP32.
- Hiện **không có sandbox cho game C++ hoặc Lua**. Native host app trong cùng process có toàn quyền máy thử nghiệm; không chạy mã dự án không tin cậy bằng engine host này.
- Các API lưu trữ, audio, mạng, key rotation, installer vẫn nằm trong lộ trình QEAPP/3. Game Snake hiện tại trong firmware v2.4.x dùng C++ nhúng + config `text` khác với demo engine M1.

## Hợp đồng bổ sung cho firmware adapter (chưa triển khai)

1. Không thay đổi đường nạp chữ ký QEAPP/2. Thiết kế ADR runtime/versioned package mới, kiểm chữ ký **trước** khi cấp quyền thực thi.
2. Tạo adapter implement `Platform`, chỉ cung cấp diện tích vẽ ứng dụng được OS cấp. Nếu toolbar/statusbar nằm ngoài app viewport, mapping tọa độ qua clip adapter.
3. GPIO → event có key repeat và debounce ở tầng OS, không bịa thêm GPIO.
4. `pause/resume/stop` phải đóng session khi MENU/Home hoặc app mất focus, trả watchdog cho firmware khi app lỗi.
5. Đo trên board: heap free/min, PSRAM high-water, render latency, input queue watermark, 10 phút soak, reboot install/update, WiFi + SD concurrent. Không dùng kết quả host để tuyên bố tương thích firmware.

## Exit gate M1 (host)

- Unit test C++ compile C++17 -Wall -Wextra -Werror -pedantic: **PASS** nếu `tests/test_engine.cpp` exit=0.
- Python host tests: **PASS** nếu golden hash của 5 screenshot trùng khớp, 1.200 tick mô phỏng không crash, `input_overflows=0` cho replay hợp lệ.
- QEAPP/2 regressions: nếu có checkout firmware và Python `cryptography`, test riêng signer roundtrip/tamper. Không có key sản phẩm trong test.
- M1 trên firmware: **NOT STARTED**; ký/chạy game Lua hay native tùy ý: **NOT SUPPORTED**.
