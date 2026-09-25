# Pocket Calculator v1.0 — báo cáo kiểm thử PC

- Bản Studio nguồn: QEAPP-Studio v0.7.4.
- Máy ảo: `qe_lua_host` biên dịch bằng g++ và **system liblua5.4.so.0** trên Linux, chẩn đoán độc lập, không phải build toolchain chính thức ESP32.
- Validate metadata Lua + guide: **2 PASS**.
- PC Lua VM vẽ 8 ảnh/8 kịch bản x 40 frame = 320 frame thực: **8 PASS**.
- Chứng cứ UI: trạng thái divide-by-zero đỏ, clear phục hồi màu, hàng kết quả lịch sử highlight: **3 PASS**.
- Ký/inspect host với P-256 private/public PEM **tạm thời**: guide text và Lua beta, **2 PASS**.
- Tổng: **15 PASS**, không bỏ qua bước nào trong bộ sample host này.
- Không chạy Windows PySide6 GUI; **không đo FPS/âm thanh/TFT thực trên ESP32-S3**, không kiểm thử cài đặt firmware stock/beta trên phần cứng.
- App không gọi API audio, file hay mạng, không giả tạo tính năng chưa được VM hỗ trợ.
- Không thay đổi bất kỳ tệp firmware hay thành phần đồ họa hệ điều hành nào.
