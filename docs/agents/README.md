# Hướng dẫn nhanh cho AI Agent — QEAPP-Studio

1. Bắt đầu ở [`../../AGENTS.md`](../../AGENTS.md); đọc hợp đồng [`../../PROMPT.md`](../../PROMPT.md) và playbook [`../../SKILLS.md`](../../SKILLS.md).
2. Xác nhận mã nguồn hiện tại theo [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md), `git status --short` và lệnh CLI thật. Firmware trong Studio là snapshot, không ghi đè checkout firmware mới chỉ vì tên đường dẫn trùng nhau.
3. Orchestrator tạo [`TASK_BRIEF_TEMPLATE.md`](TASK_BRIEF_TEMPLATE.md), giao một owner cho mỗi tệp theo [`../../agents/README.md`](../../agents/README.md).
4. Agent làm việc trong allow-list, QA chọn test IDs từ [`TEST_MATRIX.md`](TEST_MATRIX.md), ghi log/ảnh/hashes từ thao tác thực tế.
5. QA và Orchestrator hoàn thiện bản sao [`HANDOFF_TEMPLATE.md`](HANDOFF_TEMPLATE.md), nêu PASS/FAIL/SKIPPED/NOT_RUN từng tier và ký quyết định phát hành.
6. Với tài liệu, chạy `python tools/validate_agent_docs.py` trong thư mục gốc; thay đổi tài liệu cần cập nhật `DOCS_MANIFEST.json` sau khi kiểm diff.

**Cốt lõi:** firmware Back-only không được thay artwork Retro-Go; preview Lua PC không xác nhận OS chạy trên ESP32-S3; chỉ tuyên bố test đã có lệnh và bằng chứng thật.
