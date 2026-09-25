# AGENTS.md — Điều phối AI Agent cho QEAPP-Studio

> **Phạm vi:** tài liệu điều phối cho mã nguồn **QEAPP-Studio v0.7.4**; không phải yêu cầu đổi code.  Firmware đã chuyển sang repository VQEAF-OS độc lập, **không còn snapshot firmware trong Studio**; cấu hình checkout qua `QEAPP_FIRMWARE_ROOT` hoặc clone hai repo cùng cấp.  Nếu nhiệm vụ đụng firmware, xác nhận checkout nguồn đích và commit trước khi sửa.

## 0. Bắt đầu mỗi phiên

1. Đọc, theo thứ tự: [`PROMPT.md`](PROMPT.md) → [`SKILLS.md`](SKILLS.md) → [`docs/agents/PROJECT_STRUCTURE.md`](docs/agents/PROJECT_STRUCTURE.md), sau đó tài liệu của [Agent chuyên trách](agents/README.md).
2. Kiểm tra cấu trúc thật thay vì đoán (`git status --short`, tên file có thật, `python tools/qstudio.py -h`, `run_studio.bat --help` nếu launcher hỗ trợ). Xác định nguồn được phép chỉnh sửa và những thay đổi người dùng đang giữ.
3. Tạo **Task Brief** theo [`docs/agents/TASK_BRIEF_TEMPLATE.md`](docs/agents/TASK_BRIEF_TEMPLATE.md): baseline, scope, mục tiêu đo được, ràng buộc, đường dẫn/owner, test bắt buộc, tài nguyên sẵn có và điểm dừng.
4. **Không** chạy lệnh có thể xóa/chồng dữ liệu (`git reset --hard`, `git clean -fd`, force push, flash production, xóa `.venv` khỏe mạnh, tạo/ghi đè trust key) khi chưa được người dùng cho phép rõ ràng.

## 1. Điều phối: một nhiệm vụ, một owner cho mỗi tệp

**Orchestrator** (`agents/orchestrator.md`) chịu trách nhiệm tạo task brief, phân nhánh, giao công việc, quản lý xung đột và quyết định có đủ bằng chứng để chuyển giai đoạn. **Implementation Agent** chỉ sửa tập tệp được giao, không tự mở rộng phạm vi. **QA Agent** (`agents/qa-release.md`) phải kiểm tra độc lập kết quả quan trọng, xác định `PASS / FAIL / SKIPPED / NOT_RUN` trước khi handoff được chấp nhận.

| Scope / trigger | Owner chính | Vùng sở hữu mặc định | Reviewer bổ sung |
|---|---|---|---|
| `STUDIO_GUI`: IDE, Explorer, Qt, launcher, safe update | [`studio-gui.md`](agents/studio-gui.md) | `studio/gui/`, `studio/core/` liên quan, launcher/tool Qt | QA; Runtime nếu VM API thay đổi |
| `LUA_HOST_VM`: Lua 5.4 trên PC, frame protocol, input | [`lua-runtime.md`](agents/lua-runtime.md) | `runtime/`, host VM, VM tests, protocol | QA; Studio GUI nếu preview thay đổi |
| `APP_TEMPLATE`: sample/game, manifest, project | [`app-template.md`](agents/app-template.md) | `projects/`, template/test mẫu | QA; Package nếu build ký |
| `QEAPP2_STOCK`: `.qeapp` text/web, chữ ký, loader | [`package-security.md`](agents/package-security.md) | signer, parser, inspect, negative test | QA; firmware core cho loader đích |
| `LUA_BETA`: triển khai firmware Lua thử nghiệm | Lua runtime + firmware core, mỗi người tệp riêng | runtime PC hoặc firmware *được phân rõ* | Package & QA |
| `FIRMWARE_CORE`: Back, installer, bộ nhớ, FPS trên board | [`firmware-core.md`](agents/firmware-core.md) | checkout firmware cụ thể đã được xác nhận | QA; Package nếu installer |
| `TESTS_DOCS`: tài liệu, test, release | [`qa-release.md`](agents/qa-release.md) | `docs/agents/`, test harness/báo cáo | Orchestrator |

**Vùng nóng, không sửa song song:** `studio/gui/window.py`, `tools/qstudio.py`, `tools/studio_launcher.py`, `runtime/src/QeLuaRuntime.cpp`, firmware `src/main.cpp`, package format/trust anchor. Nếu có hai task đụng nhau: tuần tự hóa hoặc tạo nhánh riêng và thực hiện conflict review trên `git diff`. Không tự chọn phiên bản “mới hơn” của snapshot firmware đính kèm.

## 2. Hợp đồng bất biến (bắt buộc)

- **Đồ họa VQEAF OS:** yêu cầu chỉ cập nhật lõi / Back => giữ nguyên byte toàn bộ theme, icon, font, layout và renderer của **baseline được chỉ định**. Ghi SHA-256 trước/sau. Cơ chế Back chỉ dùng UI thông báo/hộp thoại hệ điều hành *đang có*, không vẽ lại theo Nokia/S40 khi người dùng đã yêu cầu giữ Retro-Go.
- **Phần cứng:** dùng đúng board/pin/PlatformIO environment có trong checkout thật; không tự đặt GPIO. Máy ảo PC không thay thế kiểm thử ESP32-S3, LCD, I2S hoặc SD.
- **Tương thích gói:** stock QEAPP/2 text/web và firmware Lua beta là hai năng lực khác nhau. Không được coi hình preview từ host Lua là bằng chứng bản Lua `.qeapp` chạy trên stock firmware.
- **An toàn cập nhật:** `.venv` mới phải staging + kiểm thư viện + Qt GUI probe trước khi activate; lỗi cần rollback có log. Bảo toàn dự án/config người dùng.
- **Bảo mật:** private PEM/token không xuất hiện trong source ZIP, commit, log hay screenshot; kiểm chữ ký với trust anchor thực tế chứ không dùng PEM bất kỳ rồi tuyên bố thiết bị chấp nhận.

## 3. Máy trạng thái điều phối và điểm chặn

1. **DISCOVER** — chốt repository/commit, task scope, toolchain, khả năng host/Qt/board. Nếu thiếu nguồn cần thiết, ghi `BLOCKED` và hỏi đúng dữ liệu còn thiếu; không thay thế bằng phỏng đoán.
2. **PLAN** — lập Task Brief; chốt danh sách đường dẫn được ghi, tiêu chí nghiệm thu từng giai đoạn và test IDs ở [`TEST_MATRIX.md`](docs/agents/TEST_MATRIX.md).
3. **IMPLEMENT** — owner sửa ít nhất đủ để hoàn thành. Không chỉnh file ngoài phạm vi; không che lỗi bằng `except: pass`, kết quả giả hay screenshot mockup.
4. **SELF_TEST** — owner chạy các gate tương ứng; lưu lệnh *thực tế*, exit code, môi trường và log. `NOT_RUN` nếu không có điều kiện chạy; `SKIPPED` chỉ khi test runner thật sự báo skipped có nguyên nhân.
5. **QA_REVIEW** — reviewer so diff với baseline, kiểm invariant/negative tests và tái chạy gate khả dụng. Trả lại nếu có `FAIL`, thiếu bằng chứng ở gate bắt buộc, hoặc diff ngoài scope.
6. **INTEGRATE** — orchestrator tích hợp theo thứ tự phụ thuộc, kiểm xung đột, chạy test tích hợp phù hợp; khi sửa GUI + VM cần test frame protocol; khi sửa installer cần negative signature/rollback.
7. **RELEASE_OR_HANDOFF** — chỉ phát hành với phạm vi xác minh đúng; tạo [`HANDOFF_TEMPLATE.md`](docs/agents/HANDOFF_TEMPLATE.md) điền đủ, ghi `NOT_DONE` cho commit/push chưa làm. Không ghi “device verified” chỉ từ PlatformIO PASS.

**Quy tắc chặn:** `FAIL` tại gate bắt buộc => không công bố gate đó PASS; build không đồng nghĩa flash; GUI offscreen Linux không xác minh Windows runtime; `SKIPPED` và `NOT_RUN` không được gộp thành PASS. Kết quả thiếu board luôn ghi `DEVICE: NOT_RUN` dù đã có host benchmark.

## 4. Giao tiếp giữa Agent

- Mỗi task có **một** Task Brief, **một** owner chính và **một** Handoff; QA ghi nhận kết quả trên [test matrix](docs/agents/TEST_MATRIX.md). Khi tách task, ghi rõ interface được dùng (ABI/API/manifest/frame protocol), tránh giao việc mơ hồ kiểu “làm GUI và firmware cùng lúc”.
- Chuyển giao thay đổi bằng `git diff --stat` + danh sách path + base commit + lệnh và log test. Không ghi “đã commit/đã push” nếu không có hash/log git thật.
- Nếu thay đổi không được chấp nhận: quay lại **IMPLEMENT** bằng feedback nêu cụ thể test ID, file và kết quả; không âm thầm hạ tiêu chí.
- **Khi xin duyệt:** thay đổi định dạng package, schema lưu trữ, key sản xuất, GPIO, visual freeze, reset/xóa dữ liệu hoặc flash production đều cần phê duyệt của người dùng.

## 5. Lệnh rà soát và chuẩn báo cáo

```sh
python tools/validate_agent_docs.py
python -m compileall -q studio tools
python -m unittest discover -s studio/tests -v
python -m unittest discover -s tests -v
# Nếu có PlatformIO và ĐÚNG firmware checkout:
pio run -d <confirmed-firmware-root> -e <verified-env>
```

Các lệnh trên là **lộ trình**, không phải kết quả đã chạy. Chỉ chạy test áp dụng cho scope, đánh dấu rõ mọi phụ thuộc không sẵn có. Windows GUI: `run_studio.bat --gui-check`; device: Serial 115200 + LCD video + dữ liệu FPS/heap thật. Điền thời gian, hệ điều hành, lệnh, exit code và artifact trong handoff; sử dụng báo cáo nguyên văn thay vì diễn giải số liệu không có nguồn.

**Đọc tiếp:** [`agents/orchestrator.md`](agents/orchestrator.md) (quy trình giao việc), [`docs/agents/TASK_BRIEF_TEMPLATE.md`](docs/agents/TASK_BRIEF_TEMPLATE.md) (đầu vào), [`docs/agents/HANDOFF_TEMPLATE.md`](docs/agents/HANDOFF_TEMPLATE.md) (đầu ra), [`docs/agents/TEST_MATRIX.md`](docs/agents/TEST_MATRIX.md) (release gates).
