# Quy trình phát triển ứng dụng `.qeapp` từ project tới máy thật

## Luồng chuẩn (10 giai đoạn)

| # | Giai đoạn | Việc cần hoàn thành | Gate |
|---|---|---|---|
| 01 | Chọn target | VQEAF OS v2.4.2; board ESP32-S3 N16R8; chọn web/text hoặc tính năng dự kiến Lua | Không quảng bá tương thích sai |
| 02 | New Project | `qeapp.project.json` là metadata **PC-only**; ID ASCII, version, icon và entry | `qstudio validate` |
| 03 | Edit | Text `content.txt`, web HTTPS URL; sau này Lua `src/main.lua` khi runtime sẵn sàng | Không gọi API chưa có |
| 04 | Asset import | Icon PNG **32x32** RGB được signer chuyển sang RGB565 LE; sprite/font tương lai cần định dạng đã kiểm định | Icon size, bpp, memory |
| 05 | Simulate | Ngắn hạn: host test generator, preview icon; dài hạn: C++ platform host adapter và engine thực | Ảnh phải lấy từ render engine, không mock nhận là device |
| 06 | Validate | Path hygiene, manifest constraints, size limit, type, HTTPS, dependency/version | Không path escape |
| 07 | Package & sign | `qstudio build` gọi **chính thức** `VQEAF-OS/tools/build_qeapp.py`; key P-256 ngoài repo | Header/hash/trailer hợp lệ |
| 08 | Inspect | Kiểm tra byte layout và ký bằng **public key đúng**, sửa 1 byte phải FAIL | `qstudio inspect --public-key` |
| 09 | Device install | Copy `dist/<id>.qeapp` → `SD:/System/Apps/Inbox`, trên máy App Installer → Install; tùy web/text | Firmware ghim public key cùng key-id |
| 10 | Regression & release | Reboot, test update/downgrade, storage missing/corrupt, cổng Serial 115200, thay đổi theme, phiên bản | Checklist test hardware riêng |

**Đường lỗi bắt buộc lần theo:** editor → validate → builder → file `.qeapp` → băm và chữ ký → public key firmware → SD inbox → installer → catalog → launch gate → browser/text viewer. `snake_pixel` có thêm native handler. Mất bất kỳ bước nào không được báo "cài thành công".

## Cấu trúc mã nguồn dự kiến (Studio độc lập với firmware)

```text
QEAPP-Studio/
├── PROMPT.md                 # Luật cho tác nhân AI
├── SKILLS.md                 # Quy trình theo tác vụ
├── README.md
├── studio/                   # Python + PySide6 desktop UI (giai đoạn sau)
│   ├── app.py
│   ├── views/{explorer,editor,assets,build,simulator}.py
│   ├── controllers/{project,build,debug}.py
│   └── services/{project_model,toolchain,secure_signing}.py
├── engine/                   # Engine portable: KHÔNG phụ thuộc Arduino
│   ├── include/{qe_platform.h,qe_engine.h}
│   ├── src/{loop,input,graphics,resource,app_lifecycle}.cpp
│   ├── runtime/lua/          # Tích hợp Lua sau khi duyệt format và security
│   └── platforms/{host,esp32}/
├── sdk/                      # API ổn định cho app + project profile
│   ├── api/                  # qe.* interface có phiên bản (chưa hiện thực)
│   └── profiles/vqeaf-s3-240x320.json
├── templates/{text-app,web-app,pixel-game}/
├── tools/{qstudio.py,asset_pipeline.py,verify.py}
├── tests/{unit,integration,security,golden,hardware}/
├── docs/{FORMAT,ENGINE,SECURITY,API,TESTS}.md
└── dist/                     # gitignored; KHÔNG có private keys
```

**Điểm ghép firmware:** giữ builder/signature ở `VQEAF-OS/tools/`; khối kiểm tra, data, installer trong `src/services/`; tạo module host bridge `src/services/QeappRuntimeService.*` (DỰ KIẾN), gate dispatch `src/main.cpp` và giao diện `src/apps`. Module script chỉ được link vào firmware sau khi E2E test. Không phân phát thư viện engine C++ nạp động từ SD theo kiểu DLL: ESP32 hiện chỉ chạy firmware C++ đã flash.

## Lệnh hiện có và lệnh mới trong kit

```powershell
# Từ QEAPP-Studio
py -3 tools/qstudio.py init --template text --id hello --name "Hello App" -o projects/hello
py -3 tools/qstudio.py doctor --firmware-root C:\dev\VQEAF-OS
py -3 tools/qstudio.py validate projects/web-bookmark
py -3 tools/qstudio.py build projects/web-bookmark --firmware-root C:\dev\VQEAF-OS --sign-key C:\secure\publisher.pem -o dist/web_bookmark.qeapp
py -3 tools/qstudio.py inspect dist/web_bookmark.qeapp --public-key C:\secure\publisher.pub.pem --key-id 0x31534351

# Từ VQEAF-OS (sau khi ghim public key vào firmware)
py -3 tools/verify_v242.py
pio run -e vqeaf_os
pio run -e vqeaf_os -t upload
pio device monitor -b 115200
```

Windows `/` hoặc `\` đều được Python chấp nhận ở đường dẫn. `qstudio.py` chỉ wrap web/text thật; Lua prototype sẽ bị từ chối có chủ đích.
