# QEAPP-Studio và VQEAF-OS: hai repo riêng

- **OS:** VQEAF-OS (ESP32-S3 firmware). Giữ Retro-Go launcher/icon/renderer/đồ họa.
- **Studio:** QEAPP-Studio (Windows/PySide6 IDE, Lua PC host VM, tools, samples, docs, AI Agent workflows).

## Thiết lập Windows

```powershell
# clone cùng thư mục cha:
git clone https://github.com/qeafivels/VQEAF-OS.git
git clone https://github.com/qeafivels/QEAPP-Studio.git
cd QEAPP-Studio
run_studio.bat
```

Hoặc thiết lập `QEAPP_FIRMWARE_ROOT` trỏ tới firmware bất kỳ:
`set QEAPP_FIRMWARE_ROOT=D:\Projects\VQEAF-OS`

Kiểm tra: `py -3 tools/studio_firmware.py --require`.
Khi chưa có firmware, GUI, editor và máy ảo host có thể dùng độc lập với toolchain host; các bài test signer/hardware là SKIP/NOT RUN, không được báo PASS.

Tách thư mục không đồng nghĩa OS đã hỗ trợ cài/chạy `.qeapp` Lua. Gói Lua beta cần runtime beta và kiểm thử riêng.
