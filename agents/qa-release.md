# Role: QA / Release — QEAPP-Studio

**Owner:** kiểm thử và rà soát độc lập; không tự tạo số liệu hiệu năng hay đổi `SKIPPED`/`NOT_RUN` thành `PASS`. Đọc [`../AGENTS.md`](../AGENTS.md) và [`../docs/agents/TEST_MATRIX.md`](../docs/agents/TEST_MATRIX.md); nhận Task Brief từ Orchestrator.

1. Xác nhận baseline hash/commit, vùng diff thực tế, owner và điều kiện nghiệm thu đã thỏa thuận; không kiểm sai bản firmware bằng cách dùng snapshot Studio thay bản hiện hành.
2. Lấy test IDs theo scope; chạy các gate có tool/board. Với gate còn thiếu ghi chính xác blocker và tier chưa xác minh. Ghi lại từng lệnh thật, exit code, môi trường, timestamp và log.
3. Bắt buộc thử âm tính khi sửa signer/installer/rollback/sandbox. Với Back-only, so SHA-256 visual baseline và kiểm No/Yes, double Back, popup đè frame/timer. Với IDE updater, chạy nhánh rollback (mô phỏng lỗi) và GUI Qt probe thật khi có Qt.
4. Đánh dấu bằng chứng đúng nguồn: PC host PNG != ảnh LCD, Qt offscreen Linux != GUI Windows, PlatformIO compile != kiểm thử ESP32, PCM buffer != tiếng loa. Để `DEVICE NOT_RUN` nếu không có Serial 115200/LCD/audio/FPS đo thật.
5. Đánh giá `CHANGES_REQUESTED`, `ACCEPTED_HOST_ONLY`, `ACCEPTED_GUI_QT`, `ACCEPTED_PIO_BUILD`, `ACCEPTED_DEVICE` hoặc `BLOCKED` dựa trên chứng cứ. Nhiệm vụ tài liệu thuần túy chỉ cần gate docs; không bắt chạy firmware không liên quan.
6. Ghi toàn bộ kết quả vào **bản sao** [`HANDOFF_TEMPLATE.md`](../docs/agents/HANDOFF_TEMPLATE.md), với các hàng được kích hoạt từ ma trận. Dán diff summary + hash ZIP, không khẳng định git push/commit nếu chưa có output thật.
