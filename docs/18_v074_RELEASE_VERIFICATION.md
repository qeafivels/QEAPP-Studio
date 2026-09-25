# QEAPP Studio v0.7.4 — Báo cáo kiểm thử cập nhật an toàn và GUI

Ngày: **25/09/2026**. Nền tảng chạy test: Linux, Python 3.13.5. Nguồn đầu vào: gói mã nguồn đầy đủ **QEAPP Studio v0.7.3** đã phát hành. v0.7.4 chỉ cập nhật desktop launcher, post-update GUI probe, kiểm soát venv và thử nghiệm; không thay đổi `.qeapp` firmware ABI.

## Thực hiện

- **Khởi động/kiểm tra GUI**: công cụ mới `tools/gui_post_update_check.py` dùng Qt offscreen để khởi tạo `StudioWindow` thật, tạo và mở project text tạm, thử editor, Explorer, chuyển Search/Virtual Phone và paint thực. Trên Windows còn chạy kiểm tra Qt native Windows platform DLL. JSON và PNG được tạo trên **máy người dùng khi kiểm tra thành công**; nếu thiếu Qt, ghi FAIL thay vì coi static import là kiểm thử GUI thành công.
- **Cập nhật an toàn**: runtime mới được cài vào `.qeapp_envs/env-*` tại **đường dẫn cố định**, tránh lỗi di chuyển `venv`/`pip.exe` trên Windows. Chỉ khi `pip check` + GUI probe đạt, cập nhật nguyên tử `logs/active-runtime.json`. Môi trường cũ không bị đổi; hỗ trợ `--rollback-update`, kiểm tra lock, dừng cập nhật nếu thiếu dung lượng hoặc concurrent updater, fallback nếu staging lỗi.
- **Khắc phục hỏng GUI ngay sau cập nhật**: nếu tiến trình GUI mới thoát lỗi trong 15 giây khởi động, xác minh runtime trước rồi rollback/mở GUI bản trước **một lần**; không rollback tùy tiện khi đóng GUI thường hay lỗi sau phiên dài.

## Kết quả kiểm thử thực tế trong môi trường hiện tại

| Hạng mục | Kết quả | Giới hạn |
| --- | --- | --- |
| Python compileall `tools`/`studio` | **PASS** | Kiểm tra tĩnh, không chứng minh Windows |
| `unittest discover -s studio/tests` | **92 total; 80 PASS, 12 SKIPPED** | 5 GUI tests và 1 GUI test mới SKIPPED vì thiếu PySide6; số còn lại chủ yếu thiếu Lua host binary |
| `unittest discover -s tests` | **46 total; 25 PASS, 21 SKIPPED** | Thiếu một số native/firmware dependencies để thực thi một số integration tests |
| v0.7.4 safe-update isolated regression | **15 total; 14 PASS, 1 SKIPPED** | Các ca stage/rollback là unit tests có mock, không phải nâng cấp pip thật trên Windows |
| Real GUI post-update probe trên host này | **EXPECTED FAIL / NOT VERIFIED** | PySide6 không có; script thực sự trả exit 2, xuất JSON với lỗi `ModuleNotFoundError` |
| Cài PySide6 để chạy offscreen trên host này | **KHÔNG THÀNH CÔNG** | Package index trong môi trường hiện tại không trả wheel PySide6 phù hợp; không tạo ảnh GUI giả |
| Thực thi `run_studio.bat` bằng cmd.exe trên Windows | **CHƯA CHẠY** | Cần máy Windows với PySide6 và quyền cài thư viện |
| Test máy ảo/thiết bị ESP32-S3 | **NGOÀI PHẠM VI** | Không có board gắn tại môi trường này; không xác nhận phần cứng hay FPS |

## Tái kiểm chứng trên Windows (khuyến nghị)

```bat
run_studio.bat --update-now
run_studio.bat --gui-check
run_studio.bat
```

Sau `--gui-check`, chỉ coi GUI đã kiểm chứng nếu `logs/gui-check-active.json` có `status=PASS` **và**, trên Windows, `native_windows_platform=PASS`. Nếu muốn kiểm tra bản dự phòng:

```bat
run_studio.bat --rollback-update
```

Nếu sự cố, xem `logs/launcher.log`, `logs/gui-check-*.json` và `logs/gui-crash.log`. **Không xóa `.venv` hoặc slot cũ khi đang cập nhật.**

Chi tiết kiến trúc: `docs/17_SAFE_GUI_UPDATES_v074.md` trong gói nguồn.
