# Security, QA và release gates

## Ranh giới tin cậy

`user project` (không tin cậy) → `project validator` → `asset compiler` → `trusted signer` → `QEAPP/2 package` → `signature/hash verifier on ESP32` → `transactional installer` → `verified launch gate` → `web/text / future sandbox`.

- Băm SHA-256 riêng các section không chứng minh tác giả: **phải kiểm tra ECDSA signature** với public key và key-id đã ghim firmware. Verify lại khi mở app, không chỉ lúc install.
- Single-publisher pin hiện tại có giới hạn: chưa có nhiều publisher, revocation, code isolation; roadmap QEAPP/3 phải giải quyết kiến trúc trust store mà không mở cửa cho unsigned app.
- CLI không đọc key từ project JSON, không in PEM ra log, không commit file `.pem/.key`, không phát hành khóa demo. Chọn key qua tham số CLI hoặc hệ thống keychain tương lai.
- Nếu thêm nén/asset archive: chống Zip Slip/path traversal, symlink, đệ quy sâu, decompression bomb, length overflow và path Unicode normalization; ưu tiên indexed flat archive với bound rõ.
- Tương lai Lua: vô hiệu `os.execute`, `io.popen`, `debug`, `package.loadlib`, FFI, dynamic native modules và truy cập mạng không qua capability. Hạn mức bộ nhớ/instruction/tick; kill/restore về launcher khi timeout.

## Bảng test tối thiểu

| Nhóm | Test thành công | Negative tests |
|---|---|---|
| Project schema | text/web hợp lệ và version hợp lệ | ID `../`, Unicode ID, unknown fields, invalid HTTPS, missing content |
| Package bytes | 116 header, section hashes, 76 signature trailer | magic QEAPP/1, lệch length/endian, truncated, extra trailing bytes |
| Publisher | đúng key/key-id verified | mutate byte, wrong pubkey, wrong key-id, changed installed payload |
| Install | signed v1, signed v2 update và reboot | downgrade, no SD, storage full, interrupted `.stage/.backup`, unexpected files |
| App data | đúng 3 slot và ID verified | sai ID, unknown slot, >16KiB/slot, >32KiB tổng, path traversal |
| UI/Engine | 240x320 clip, font UTF support nếu thêm, key repeat | rapid keys, MENU interrupt, SELECT long, insufficient PSRAM |
| Fuzz | deterministic corpus, bounded parsing | malformed manifest/image/resource/bytecode, large allocation request |
| Device | ST7789 real display, SD_MMC, NTP/TLS and input | radio drop, card remove, power loss in safe test environment |

Chạy `py -3 -m unittest discover -s tests -v` trong kit. E2E signer test tạo key P-256 tạm thời **trong thư mục temp** và dùng `VQEAF-OS/tools/build_qeapp.py` thật. Không sửa firmware production key trong test CLI.

## Quy cách báo cáo

Mỗi tác vụ phải có: baseline commit SHA, commit mới (nếu thực sự push), firmware branch, environment, SHA-256 artifact, count PASS/FAIL, lỗi còn mở, phân loại `HOST_TESTED` vs `ESP32_VERIFIED`. Screenshot host phải đề "host renderer"; hình mockup không phải screenshot. Báo cáo không tuyên bố build PlatformIO thành công nếu không thực sự chạy.

## Điều kiện phát hành độc lập game/app (M5 trở lên)

Chỉ công bố hỗ trợ `.qeapp` game Lua độc lập khi: package spec mới được duyệt, verify/signature/hạn mức PASS, runtime firmware thật đã tích hợp, 2 games + 1 utility chạy trên ESP32-S3 qua SD, test reboot/pause/resume/input + perf soak và artifact mở đúng bằng firmware có version phù hợp. Các milestone trước đó là alpha/design.
