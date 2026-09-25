# TASK BRIEF — QEAPP-Studio (sao chép cho mỗi nhiệm vụ)

> **Mẫu chưa thực hiện**: không điền PASS cho phần nào nếu chưa có lệnh/bằng chứng.

| Trường | Giá trị cần điền |
|---|---|
| Task ID / tiêu đề | `<QE-YYYYMMDD-001> / <feat|fix|test|docs: mục tiêu>` |
| Người yêu cầu / Orchestrator | `<yêu cầu gốc> / <agent phụ trách>` |
| Repository và baseline | `<đường dẫn repo, git SHA hoặc hash ZIP thực tế>` |
| Phiên bản đích | `<Studio x.y.z / firmware tag+commit nếu có>` |
| Nhãn phạm vi | `STUDIO_GUI / LUA_HOST_VM / APP_TEMPLATE / QEAPP2_STOCK / LUA_BETA / FIRMWARE_CORE / TESTS_DOCS` |
| Trạng thái ban đầu | `PLANNED` |
| Owner / reviewer | `<một owner chính> / <QA>` |
| Nguồn yêu cầu | `<trích mô tả chức năng, không tự suy diễn thành phần khác>` |
| Phần cứng/công cụ sẵn có | `<OS/Python/Qt/Lua/PIO/board/Serial; UNKNOWN nếu chưa biết>` |

## Mục tiêu có thể đo được

- **Before:** `<lỗi hoặc hành vi trước thay đổi và bằng chứng>`
- **After:** `<hành vi cần đạt; tiêu chí khách quan>`
- **Ngoài phạm vi:** `<những gì tuyệt đối không chỉnh>`
- **Tệp được ghi (allow-list):** `<đường dẫn thực tế sau khi kiểm tra>`
- **Tệp read-only / visual freeze:** `<pattern + đường dẫn danh sách SHA-256 đầu vào nếu có>`
- **Dependency tasks và interface:** `<Task ID + public API/schema/protocol>`

## Kiểm thử/điểm chặn được chốt trước

| Test ID (tra TEST_MATRIX.md) | Áp dụng? | Gate bắt buộc? | Bằng chứng dự kiến | Người thực thi |
|---|---|---|---|---|
| `<PY01 / QT01 / FW01...>` | `YES/NO` | `YES/NO` | `<log, PNG, Serial...>` | `<owner/QA>` |

## Rủi ro, rollback và phê duyệt

- **Rủi ro:** `<OOM, reset, thay đổi package/trust, mất dữ liệu, xung đột nhánh...>`
- **Rollback:** `<chỉ cách quay về phiên bản trước, không xóa dữ liệu>`
- **Cần người dùng duyệt trước:** `<không có / flash / thay GPIO / package version / keys / đổi UI>`
- **Điều kiện dừng:** `<thiếu baseline, FAIL bắt buộc, sai phạm vi>`
- **Tiêu chí bàn giao:** `<source diff + completed handoff + test matrix rows + log/ảnh thật>`
