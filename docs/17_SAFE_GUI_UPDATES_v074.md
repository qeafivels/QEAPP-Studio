# QEAPP Studio v0.7.4 — kiểm tra GUI thực sau cập nhật + môi trường cập nhật an toàn

**Đối tượng:** QEAPP Studio Windows desktop Python/PySide6. **Không flash firmware**, không sửa định dạng `.qeapp`, không chứng minh FPS trên ESP32-S3.

## Khi nhấp đúp `run_studio.bat`

1. Tìm Python 3.10+ x64, sử dụng `.venv` hoặc runtime đã kích hoạt qua `logs/active-runtime.json`.
2. Kiểm tra `pip`, phiên bản PySide6/Pillow/cryptography và `pip check` trên interpreter đang dùng. **Không nâng cấp trực tiếp runtime còn chạy tốt.**
3. Chạy `tools/gui_post_update_check.py` bằng interpreter đó, trên Qt `offscreen` trong **tiến trình riêng**. Script tạo thật `QApplication`, mở và paint `StudioWindow`, tạo dự án text tạm, mở một file, chuyển Explorer/Search/Virtual Phone, xác nhận LCD 240×320. Config được cô lập trong thư mục tạm; không đọc/sửa project người dùng. Trên Windows, launcher còn yêu cầu Qt Windows platform plugin khởi tạo thành công ở tiến trình riêng. Nếu thiếu Qt, báo FAIL chứ không tuyên bố đã test GUI.
4. Nếu có gói mới theo lịch 24 giờ (hoặc `--update-now`), tạo một `venv` **ở đường dẫn cố định** `.qeapp_envs/env-<timestamp>-<pid>`. Không `copy`, không `rename` venv trên Windows: pip launchers có đường dẫn tuyệt đối. Cài mọi gói từ `requirements-studio.txt` với wheel nhị phân, `pip check`, rồi lặp lại GUI test thật **trong venv mới**.
5. Chỉ sau PASS mới chuyển atomically `logs/active-runtime.json` đến slot mới; vẫn giữ bản cũ và toàn bộ project. `logs/runtime-update.lock` ngăn hai trình nâng cấp cùng lúc.
6. Nếu cài đặt/GUI test thất bại: giữ interpreter đang chạy tốt, dọn **chỉ staging mới sinh**, tiếp tục mở GUI cũ. Nếu runtime cũ cũng hỏng: báo lỗi và dừng. Nếu GUI vừa kích hoạt thoát lỗi trong 15 giây đầu, launcher thử kiểm tra + rollback và mở bản cũ một lần.

## Các lệnh

```bat
run_studio.bat                     REM tự kiểm tra, cập nhật an toàn khi đến lịch và chạy
run_studio.bat --update-now        REM cập nhật trong môi trường mới, kiểm tra GUI, mới kích hoạt
run_studio.bat --gui-check         REM chỉ kiểm tra GUI offscreen + ảnh thật, không cài/cập nhật
run_studio.bat --rollback-update   REM kiểm chứng và quay về runtime cũ còn hoạt động
run_studio.bat --offline          REM chỉ dùng dependency đang có, không kết nối mạng
run_studio.bat --diagnose         REM chẩn đoán không sửa môi trường
```

`--repair` vẫn sao lưu thiết lập lỗi. `--reinstall-deps` giờ cài mới ở môi trường staging thay vì bắt buộc ghi vào `.venv` đang ổn định. `--system` chỉ kiểm tra: cập nhật gói Python hệ thống không bảo đảm an toàn và bị từ chối.

## Log và bằng chứng

- `logs/launcher.log` — mọi bước chọn runtime / cập nhật / phát hiện rollback.
- `logs/active-runtime.json` — runtime đã qua kiểm tra; `previous` chỉ đặt khi runtime cũ thực sự healthy.
- `logs/dependency-update-state.json` — lịch thử/success; thất bại back-off 6 giờ, success kiểm tra tiếp sau 24 giờ.
- `logs/gui-check-active.json`, `logs/gui-check-stage-<id>.json`, `logs/gui-check-rollback.json` — báo cáo kiểm tra thực của Qt. Ảnh PNG chỉ được tạo khi render offscreen thực sự thành công; **không phải ảnh minh họa hay ESP32-S3**.
- `logs/gui-crash.log`, `logs/gui-errors.log` — chẩn đoán GUI.

Khuyến cáo sau cập nhật: chạy `run_studio.bat --gui-check`, xem kết quả `PASS` và mở IDE bằng `run_studio.bat` trên Windows thật. Kiểm thử vỏ GUI bằng Qt offscreen không thay thế điều khiển chuột/bàn phím thực tế. Các môi trường trong `.qeapp_envs/` chiếm thêm đĩa để có thể rollback; chỉ xóa thủ công slot không còn active/previous, khi IDE không chạy. Nếu `runtime-update.lock` còn lại sau crash, chỉ xóa khi chắc chắn không có launcher đang cập nhật.
