# HANDOFF TEMPLATE — Bàn giao giữa AI Agent (mẫu điền)

> **Không điền kết quả giả:** mọi giá trị `<...>` phải được thay bằng kết quả thật; khi chưa kiểm chứng ghi `NOT_RUN`. Mỗi task giữ một bản sao riêng tại `reports/agent_handoffs/<TASK_ID>.md` (tạo thư mục khi cần). Không commit log chứa thông tin nhạy cảm.

## 1. Định danh và phạm vi

| Trường | Giá trị |
|---|---|
| Task ID / tiêu đề | `<ID> / <mục đích>` |
| Nguồn Task Brief | `<path hoặc tham chiếu>` |
| Owner → Reviewer → Orchestrator | `<role/name → role/name → role/name>` |
| Baseline repo/commit/ZIP SHA-256 | `<repo, SHA/tag cụ thể>` |
| Đích áp dụng | `Studio <version> / firmware <version+SHA> / host-only` |
| Nhãn scope | `STUDIO_GUI / LUA_HOST_VM / APP_TEMPLATE / QEAPP2_STOCK / LUA_BETA / FIRMWARE_CORE / TESTS_DOCS` |
| Nhánh / commit / tình trạng push | `<branch> / <hash hoặc NOT_DONE> / <remote receipt hoặc NOT_DONE>` |
| Môi trường | `<OS, Python, Qt, Lua, PIO, board, toolchain version>` |
| Ngày giờ kiểm thử và timezone | `<ISO8601 + offset>` |
| Trạng thái | `READY_FOR_QA / CHANGES_REQUESTED / ACCEPTED / BLOCKED` |

## 2. Những gì thực sự đã thay đổi

**Mục tiêu & kết quả:** `<trước → sau, có thể kiểm chứng>`

| Tệp | Loại thay đổi | Giải thích / owner |
|---|---|---|
| `<path từ repo gốc>` | `NEW/MODIFIED/DELETED` | `<thay đổi thật>` |

- **File thay đổi ngoài allow-list:** `<không có / danh sách + phê duyệt>`
- **Interface/ABI/format:** `<không thay đổi / mô tả + migrations>`
- **Ứng dụng stock và beta:** `<phân biệt rõ tương thích>`
- **Rollback:** `<lệnh hoặc trình tự có thể đảo ngược, đề cập trạng thái lưu>`
- **Bí mật:** `<scan khóa/PEM/token, kết quả; không chèn dữ liệu thật vào đây>`
- **Ảnh UI giữ nguyên (đối với firmware core-only):** `<đường dẫn danh sách hash trước/sau, số file/khác biệt; nếu không áp dụng: N/A>`

## 3. Ma trận kết quả thực thi

Sao chép các dòng **được kích hoạt** từ [`TEST_MATRIX.md`](TEST_MATRIX.md); thêm test ID custom với tiêu chí đo được. Phải ghi được lệnh chạy lại và log/ảnh *thật*.

| ID | Mức (`STATIC/HOST/GUI_QT/PIO_BUILD/DEVICE`) | Lệnh hoặc thao tác đã thực hiện | Kết quả + exit code | Số liệu/case | Đường dẫn bằng chứng | Chưa kiểm vì sao |
|---|---|---|---|---|---|---|
| `<PY01>` | `STATIC` | `<python -m compileall ...>` | `NOT_RUN` | `—` | `—` | `<lý do nếu chưa chạy>` |
| `<QT01>` | `GUI_QT` | `<run_studio.bat --gui-check>` | `NOT_RUN` | `—` | `—` | `<lý do nếu chưa chạy>` |
| `<DEV01>` | `DEVICE` | `<thao tác và Serial 115200>` | `NOT_RUN` | `—` | `—` | `<lý do nếu chưa chạy>` |

**Quy ước:** `PASS`=đã thực hiện và đạt tiêu chí; `FAIL`=đã thực hiện nhưng không đạt; `SKIPPED`=runner bỏ qua và phải có lý do; `NOT_RUN`=không thực hiện. Không cộng SKIPPED vào PASS. Với hiệu năng ghi số mẫu, trung bình/p95, điều kiện tải, baseline và sai số; không suy diễn FPS thiết bị từ host.

## 4. Kiểm tra âm tính, hồi quy và trực quan

- **Negative tests đã chạy:** `<package tamper, fail update/rollback, invalid input, OOM... kèm ID/log>`
- **Số liệu phần cứng:** `<Serial port, tốc độ 115200, reset reason, heap/PSRAM, FPS; hoặc DEVICE NOT_RUN>`
- **Chứng cứ giao diện:** `<ảnh Qt THỰC và môi trường chụp; mockup đánh nhãn minh họa>`
- **Chứng cứ LCD/âm thanh:** `<video thiết bị và file thu âm, hoặc NOT_RUN>`
- **Các thay đổi đã tác động đến gate nào:** `<ID + lý do>`
- **Regression còn mở:** `<mã lỗi + mức ưu tiên + issue/owner>`

## 5. Xác nhận của reviewer / quyết định tích hợp

| Câu hỏi | Kết quả (`YES/NO/NOT_RUN`) | Minh chứng |
|---|---|---|
| Baseline đúng bản được giao? | `NOT_RUN` | `<commit/hash>` |
| Không xâm phạm diff khác / ngoài scope? | `NOT_RUN` | `<git diff --stat>` |
| Test bắt buộc không có FAIL? | `NOT_RUN` | `<matrix + logs>` |
| Không có khóa riêng, token trong gói? | `NOT_RUN` | `<scan summary>` |
| Giữ nguyên artwork Retro-Go nếu core-only? | `NOT_RUN` | `<SHA-256 trước/sau>` |
| Có đủ bằng chứng để khẳng định trên thiết bị? | `NOT_RUN` | `<Serial+LCD/âm thanh>` |

- **QA verdict:** `CHANGES_REQUESTED / ACCEPTED_HOST_ONLY / ACCEPTED_GUI_QT / ACCEPTED_PIO_BUILD / ACCEPTED_DEVICE / BLOCKED`
- **Orchestrator decision:** `INTEGRATE / HOLD / RETURN_TO_OWNER`
- **Thông tin còn thiếu và người thực hiện tiếp:** `<task dependency hoặc gate>`

## 6. Mẫu mô tả commit và giao hàng

```text
<feat|fix|docs|test|perf>: <nội dung gọn>

Why: <lỗi/yêu cầu>
What: <file/behavior chính>
Tests: <ID PASS; ID SKIPPED/NOT_RUN, điều kiện>
Limits: <giới hạn xác minh>
```

**Bàn giao:** `<diff/patch/source ZIP thực tế>`; **SHA-256:** `<hash>`; **Push:** `NOT_DONE` trừ khi có output git xác nhận. Không đưa đường dẫn sandbox không tồn tại vào báo cáo.
