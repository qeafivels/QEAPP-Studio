# QEAPP-Studio AI Agent Kit v1.1 — hướng dẫn cài đặt

Bộ này cập nhật **AGENTS.md điều phối**, **mẫu Task Brief/Handoff** và **Test Matrix**, kế thừa `PROMPT.md`/`SKILLS.md` v1.0. Đây là **chỉ tài liệu + công cụ kiểm tra tài liệu**, không thay source Studio, VM hoặc firmware. Base: QEAPP-Studio v0.7.4 AI Agent Ready; bản VQEAF OS mới phải được lấy riêng và xác nhận nếu có nhiệm vụ firmware.

## Cài đặt

1. Sao lưu các tài liệu đã chỉnh sửa trong checkout đích.
2. Giải nén bản cập nhật v1.1 vào **gốc QEAPP-Studio** (nơi có `run_studio.bat`), giữ nguyên cấu trúc thư mục `agents/`, `docs/agents/` và `tools/`.
3. Chạy `python tools/validate_agent_docs.py`. Xem stdout và xử lý đường dẫn nếu project đã tổ chức lại.
4. Agent đọc `AGENTS.md` → `PROMPT.md` → `SKILLS.md` → vai trò trong `agents/`.
5. Với mỗi task, tạo bản sao `docs/agents/TASK_BRIEF_TEMPLATE.md` và `docs/agents/HANDOFF_TEMPLATE.md` trong thư mục báo cáo riêng (không viết đè mẫu). Điền test run từ `docs/agents/TEST_MATRIX.md`.

## Không làm

Không ghép bản firmware tham chiếu trong Studio lên checkout VQEAF OS v2.5.1/Back r2 hiện có. Không tự chạy `git clean`, reset hay flash. Tất cả bài test docs chạy trên PC chỉ kiểm **tài liệu**, không xác nhận GUI/ESP32-S3.

## Phân biệt gói

- **Agent Kit Update**: chỉ file tài liệu và validator liên quan — dùng nếu đã có Studio.
- **AI Agent Full Source**: Studio v0.7.4 kết hợp docs v1.1; **không** chứa những bản OS mới được triển khai sau khi v0.7.4 đóng gói.
