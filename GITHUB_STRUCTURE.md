# QEAPP-Studio — repository độc lập

Repository này là **desktop IDE**, không phải firmware. Không chứa bản sao VQEAF-OS.

```text
qeafivels/
  VQEAF-OS/      # firmware ESP32-S3, giao diện Retro-Go
  QEAPP-Studio/  # PySide6 IDE + Lua host VM + mẫu Pocket Focus/Calculator
```

Clone hai repository cùng thư mục cha hoặc đặt `QEAPP_FIRMWARE_ROOT` tới thư mục firmware có `platformio.ini`. Mọi lệnh ký/cài `.qeapp` dùng nguồn firmware từ repository **VQEAF-OS**, không giả định một bản copy trong Studio. Host Lua Preview có thể chạy không có firmware nếu dùng system Lua để chẩn đoán hoặc có Lua nguồn đã cài đặt.

Ứng dụng Lua chạy trên máy ảo PC **chưa đồng nghĩa** đã được kiểm thử trên ESP32-S3. Giữ nguyên giao diện Retro-Go trong OS; repo Studio chỉ tác động firmware khi có nhiệm vụ và kiểm thử riêng.

Mã nguồn được di chuyển từ `qeafivels/VQEAF-OS` nhánh `feat/qeapp-studio-samples-v074`, commit `68bd31e1cfb4e1b17d03679b0c3871f2a4b6ed7d`; đã chuyển 221 tệp gốc trước khi sửa các đường dẫn phụ thuộc firmware để chạy độc lập.
