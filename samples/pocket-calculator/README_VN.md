# Pocket Calculator v1.0 — ứng dụng mẫu QEAPP-Studio

Mẫu thứ hai sau Pocket Focus: ứng dụng **máy tính bỏ túi** điều khiển hoàn toàn bằng D-pad, viết Lua 5.4 và đồ họa RGB565 dạng pixel. Thực thi đã kiểm tra qua QEAPP-Studio v0.7.4 PC host trên Linux; **chưa** kiểm chứng GUI PySide6 Windows hay thiết bị ESP32-S3.

![Ảnh kết quả chạy thực qua PC Lua VM](screenshots/00_OVERVIEW_ACTUAL_PC_VM.png)

## 1. Cấu trúc

```text
PocketCalc_QEAPP_Studio_Sample/
├── README_VN.md
├── CHANGELOG.md
├── docs/01_QEAPP_STUDIO_STRUCTURE.md
├── projects/
│   ├── pocket-calculator-lua/
│   │   ├── qeapp.project.json   # metadata được qstudio.py xác nhận
│   │   ├── main.lua             # toàn bộ logic & UI, không require/dofile
│   │   ├── assets/icon.png      # 32 x 32 PNG
│   │   └── tests/*.json         # 8 scenario phím tái hiện
│   └── pocket-calculator-guide/
│       ├── qeapp.project.json   # bản hướng dẫn text dành cho stock OS
│       ├── content.txt
│       └── assets/icon.png
├── screenshots/               # ảnh thực của PC Lua VM, không phải ESP32
├── reports/host_test_results.json
├── tests/verify_sample.py
├── run_example.bat
└── run_host_test.bat
```

Cấu trúc **toàn bộ Studio** nằm trong `docs/01_QEAPP_STUDIO_STRUCTURE.md`.

## 2. Tính năng

- Trang Home, Calculator, History, About.
- Cộng/trừ/nhân/chia, số thập phân, đổi dấu, nút DEL và Clear.
- Xử lý chia cho 0 và kết quả lớn quá ngưỡng; không để crash.
- Lưu 5 kết quả **trong RAM phiên chạy**; cho phép chọn kết quả để tính tiếp.
- Render bằng `engine.clear`, `engine.rect`, `engine.text`; không phụ thuộc network, SD, audio hay thư viện Lua ngoài VM.
- Không bắt sự kiện Back/Home cấp hệ điều hành, không thay thế popup hoặc giao diện Retro-Go đang dùng.

## 3. Điều khiển

- D-pad: di chuyển giữa các nút hoặc các hàng lịch sử.
- START: chọn nút / thực hiện phép tính / mở một màn hình.
- OPTION: quay lại trang ứng dụng.
- **Back/Home vật lý**: do hệ điều hành xử lý, không gửi xuống Lua khách.
- Ở trang Calculator, nhấn START tại nút `HIST` để xem lịch sử. Chọn lịch sử rồi START để tái sử dụng kết quả.

## 4. Mở bằng Studio (Windows)

Cần giải nén bản **QEAPP-Studio v0.7.4 Full Source** riêng và chạy `run_studio.bat`. Trong bộ mẫu này nhấp `run_example.bat` hoặc mở project thủ công:

`PocketCalc_QEAPP_Studio_Sample/projects/pocket-calculator-lua`

Trong IDE: `F6` Validate, `F9` chạy máy ảo PC Lua. Nếu máy báo thiếu công cụ, dùng script khởi chạy Studio để cài phụ thuộc, sau đó chạy `run_host_test.bat` để kiểm tra sample. Script không thay đổi các file hệ điều hành.

## 5. Chạy headless và chụp hình thật trên PC

Ví dụ khi terminal đang ở Studio root:

```bat
python tools\lua_preview.py "C:\path\PocketCalc_QEAPP_Studio_Sample\projects\pocket-calculator-lua\main.lua" --frames 40 --replay "C:\path\PocketCalc_QEAPP_Studio_Sample\projects\pocket-calculator-lua\tests\result_7_plus_2.json" -o calc_result.png
```

Công cụ khởi chạy **Lua VM thật** và chuyển RGB565 thành PNG 240x320 (29 dòng top/21 dòng bottom là chrome mô phỏng, phần guest thật 240x270).

## 6. Ký gói .qeapp

- Gói `pocket-calculator-guide`: `type=text`, có thể ký bằng **private PEM do bạn quản lý** cùng key-id/public key **đúng trust-anchor firmware stock**. Không sử dụng khóa ký thử nghiệm được sinh từ báo cáo host để cài vào board.
- Gói `pocket-calculator-lua`: `type=lua`, **beta riêng**, cần `--experimental-lua` và board cài `vqeaf_lua_beta`. Firmware stock không thể chạy app Lua tương tác này.
- Không gửi private key cho người khác và không commit private key vào Git; test tạo khóa tạm chỉ để kiểm chứng packer/inspect trên PC.

```bat
python tools\qstudio.py build "C:\path\PocketCalc_QEAPP_Studio_Sample\projects\pocket-calculator-lua" --firmware-root firmware\VQEAF-OS --sign-key C:\secure\publisher.pem --key-id 0x544c5541 --experimental-lua -o C:\build\pocket_calc.qeapp
```

Khóa công khai beta và ID phải khớp chính xác khóa đã tích hợp vào firmware trên thiết bị. Hãy kiểm tra bằng `qstudio.py inspect` với **public PEM tương ứng** trước khi chuyển sang thẻ nhớ, và tiếp tục xác nhận chính sách tin cậy của firmware trên thiết bị thật.

## 7. Kết quả test

Script `tests/verify_sample.py` đã chạy host 8 kịch bản thực tế × 40 frame, 2 validate, 3 kiểm tra pixel UI và 2 phép ký/kiểm chữ ký QEAPP/2 sử dụng khóa **tạm thời** = 15 phép kiểm PASS. Máy ảo chạy bằng `--system-lua` chỉ là phép chẩn đoán Linux, chưa chứng minh Windows GUI/board thực.

Xem `reports/host_test_results.json` và ảnh trong `screenshots/`.
