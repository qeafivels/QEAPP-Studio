# Tách QEAPP-Studio ra khỏi VQEAF-OS

**Trạng thái lúc đóng gói:** dự án QEAPP-Studio **chưa được tạo trực tuyến**; GitHub connector hiện tại có quyền đẩy mã vào repo có sẵn nhưng không có thao tác tạo repo. Không xóa source bên OS trước khi repo mới được xác minh.

## Bước 1: Đưa Studio lên GitHub

Giải nén ZIP vào thư mục `QEAPP-Studio`. Cài Git for Windows + GitHub CLI + Python 3.10+, mở terminal, chạy `gh auth login` (xác thực qua trình duyệt) và `PUBLISH_STUDIO.bat`. Script sẽ tạo repo `qeafivels/QEAPP-Studio` public (hoặc `PUBLISH_STUDIO.bat private` để tạo private), commit bằng identity Git của bạn, push toàn bộ source và kiểm tra từng tệp từ GitHub bằng git blob SHA. Nếu repo đã có sẵn, script push `main` không force. Hãy tạo repo **trống**, không chọn thêm README hoặc license. Nếu script gặp lỗi, dừng; không cần xóa bất cứ tệp nào ở OS.

## Bước 2: Kiểm tra độc lập

`py -3 tools/verify_separation.py --verify-remote` phải PASS. Clone `VQEAF-OS` cạnh `QEAPP-Studio` hoặc thiết lập `QEAPP_FIRMWARE_ROOT` bằng thư mục firmware bên ngoài. GUI có thể chạy không có firmware, chức năng ký cần checkout OS.

## Bước 3: Dọn nhánh cũ của OS

Chỉ sau khi bước 2 PASS, chạy `CLEAN_OS_FEATURE_BRANCH.bat`. Script xác thực GitHub đã nhận đủ tệp, kiểm tra SHA chính xác của **nhánh tích hợp cũ**, chỉ xóa `developer/QEAPP-Studio` trong **nhánh `feat/qeapp-studio-samples-v074`** và thêm liên kết tới repo mới. **`VQEAF-OS/main` không bị sửa.** Nếu nhánh cũ đã có commit khác, script dừng để tránh mất công sức của người khác.

## Bước 4: Dọn scaffold trên OS main (chỉ sau khi đã xác minh mới)

OS `main` hiện chỉ có một tệp cũ `developer/QEAPP-Studio/GITHUB_STRUCTURE.md` trong thư mục Studio. Chạy `CLEAN_OS_MAIN_SCAFFOLD.bat` sau khi bước 2 PASS. Script xác thực SHA hiện tại của main + chỉ đúng 1 tệp scaffold rồi mới xóa tệp đó và thêm một liên kết ở `docs/`, không xóa firmware hoặc đồ họa. Nếu main thay đổi trước đó, script dừng và yêu cầu rà soát thủ công.

## Cấu trúc độc lập

```
workspace/
├── VQEAF-OS/           # ESP32-S3 firmware / Retro-Go UI
└── QEAPP-Studio/      # IDE, runtime PC, projects, samples, agents
    ├── studio/
    ├── runtime/
    ├── engine/
    ├── projects/
    ├── samples/pocket-focus/
    └── samples/pocket-calculator/
```

Các phép kiểm thử trên PC không chứng minh khả năng chạy `.qeapp` Lua ở thiết bị thật.
