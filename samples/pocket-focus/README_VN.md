# Pocket Focus v1.0 — ứng dụng Lua mẫu cho QEAPP Studio

Một ứng dụng hẹn giờ tập trung / nghỉ giải lao dành cho vùng vẽ 240×270 của máy ảo QEAPP Studio v0.7.4. Đây là ứng dụng **tương tác thật trên máy ảo Lua PC** (không phải giao diện giả lập bằng ảnh). Các thành phần: menu chính, hẹn giờ có Start/Pause, thời lượng định sẵn, nghỉ tự động, thống kê phiên hiện tại, About, hộp thoại xác nhận kết thúc phiên, icon 32×32.

## Cấu trúc

```
projects/
  pocket-focus-lua/
    qeapp.project.json   # dự án type=lua, chỉ dành cho firmware beta có Lua VM
    main.lua             # ứng dụng hoàn chỉnh, duy nhất một file
    assets/icon.png      # icon PNG 32×32, sẽ đóng gói thành RGB565
    tests/*.json         # kịch bản nhập phím tái lập
  pocket-focus-guide/
    qeapp.project.json   # type=text: tài liệu cài được trên QEAPP/2 stock
    content.txt          # tài liệu đọc offline trên thiết bị
    assets/icon.png
screenshots/             # các frame thực tế từ PC Lua VM
scripts/
tests/verify_sample.py
```

## Mở trong QEAPP Studio 0.7.4 (Windows)

1. Giải nén ZIP này ở bất cứ đâu (không ghi đè hoặc thay đổi mã nguồn hệ điều hành).
2. Mở `run_studio.bat` từ mã nguồn Studio v0.7.4; hoặc chạy `run_example.bat` trong ZIP này, nhập đường dẫn Studio nếu được hỏi.
3. Chọn **File → Open Project** và mở đúng thư mục `projects/pocket-focus-lua` chứa `qeapp.project.json`.
4. Mở `main.lua` bằng Explorer, chỉnh sửa → `Ctrl+S` để lưu → `F6` để Validate → `F9` để chạy máy ảo tương tác. Trên một số bản Studio, `F8` chạy PNG deterministic replay.
5. Phím: `↑↓` chọn menu; `START` xác nhận/tạm dừng/tiếp tục; `←→` chỉnh lựa chọn Settings, hoặc chọn `YES/NO`; `OPTION` trở về hoặc yêu cầu kết thúc timer.
6. **Back/Menu/Home thuộc OS** và không được script nhận. Thông báo thoát của VQEAF OS dùng giao diện gốc, không bị app thay đổi.

Từ terminal tại thư mục **gốc Studio** để xác thực và dựng PNG:

```bat
py -3 tools\qstudio.py validate C:\Path\PocketFocus\projects\pocket-focus-lua
py -3 tools\bootstrap_lua.py
py -3 tools\build_lua_host.py
py -3 tools\qstudio.py lua-preview C:\Path\PocketFocus\projects\pocket-focus-lua --frames 30 --replay tests/running.json -o C:\Path\PocketFocus\screenshots\manual.png
```

Hoặc từ thư mục mẫu:

```bat
py -3 tests\verify_sample.py --studio C:\Path\QEAPP-Studio-v0.7.4
```

`--system-lua` của script kiểm thử chỉ được dùng để chẩn đoán Linux có thư viện Lua 5.4 của hệ thống. Bản chính thức yêu cầu Lua chuẩn được bootstrap bằng công cụ Studio.

## Đóng gói thực tế lên VQEAF OS

**A. Stock firmware v2.5.1 / Back r2:** Có thể đóng gói **Pocket Focus Guide (type=text)** bằng khóa P-256 tin cậy **khớp public key đang ghim trong firmware**. Chương trình hẹn giờ tương tác KHÔNG chạy bằng gói text và KHÔNG cài như app Lua trên stock OS.

```bat
py -3 tools\qstudio.py build C:\Path\PocketFocus\projects\pocket-focus-guide --firmware-root C:\Path\VQEAF-OS --sign-key C:\SecureKeys\your-stock-publisher-private.pem --key-id YOUR_REAL_STOCK_KEY_ID -o C:\Path\PocketFocus\dist\pocket-guide.qeapp
py -3 tools\qstudio.py inspect C:\Path\PocketFocus\dist\pocket-guide.qeapp --public-key C:\SecureKeys\your-stock-public.pem --key-id YOUR_REAL_STOCK_KEY_ID
```

**B. Bản thử nghiệm `vqeaf_lua_beta`:** Chỉ khi bạn **đã có firmware riêng** với `src/lua/QeLuaRuntime.cpp`, bật Lua và đã ghim public key beta hợp lệ, bạn mới thử build gói Lua:

```bat
py -3 tools\qstudio.py build C:\Path\PocketFocus\projects\pocket-focus-lua --experimental-lua --firmware-root C:\Path\VQEAF-LUA-BETA --sign-key C:\SecureKeys\your-lua-beta-private.pem --key-id YOUR_REAL_LUA_BETA_KEY_ID -o C:\Path\PocketFocus\dist\pocket-focus-beta.qeapp
```

**Không** sử dụng khóa test tạm do bộ kiểm thử tạo để cài trên thiết bị; kiểm chữ ký trên PC với public PEM bất kỳ không chứng minh firmware thật chấp nhận. Dữ liệu thống kê chỉ nằm trong RAM phiên chạy, chưa lưu sau khi thoát vì API storage/file của guest chưa có. Không có audio guest API hay RTC, nên không tuyên bố phát âm thanh hoặc đồng bộ thời gian thực khi OS ngủ.

## Kiểm thử được thực hiện

- Kiểm tra cấu trúc dự án bằng `tools/qstudio.py validate` của Studio v0.7.4.
- Chạy nhiều nhánh giao diện cùng engine C++ Lua 5.4 và xuất PNG frame thực, thử giới hạn heap thông qua thống kê VM.
- Kiểm thử luồng kết thúc phiên bằng test fixture rút ngắn thời gian **chỉ trong thư mục tạm** (không thay đổi bản release).
- Đóng gói chữ ký ECDSA P-256 bằng khóa **chỉ tồn tại trong thư mục tạm** và inspect host; không đưa khóa riêng/test `.qeapp` vào ZIP.
- Chưa chạy GUI PySide6 Windows, PlatformIO trên thiết bị thật, ST7789 hoặc âm thanh phần cứng.
