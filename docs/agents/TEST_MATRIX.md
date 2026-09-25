# TEST MATRIX — QEAPP-Studio / VQEAF OS (mẫu QA + quy tắc release)

> **MẪU, KHÔNG PHẢI KẾT QUẢ KIỂM THỬ.** Bản này áp dụng cho Studio v0.7.4 và các phiên bản firmware **được chỉ định cụ thể**. Chỉ chuyển dòng có liên quan sang bản test run trong handoff; đặt trạng thái ban đầu `NOT_RUN`. Kết quả cũ trên ZIP khác không tự động chuyển thành PASS cho bản mới.

## 1. Quy tắc sử dụng

- **Scope** là `STUDIO_GUI`, `LUA_HOST_VM`, `APP_TEMPLATE`, `QEAPP2_STOCK`, `LUA_BETA`, `FIRMWARE_CORE`, `TESTS_DOCS`; task có thể chứa nhiều scope nhưng cần tách tệp owner.
- **Tier**: `STATIC` (source/docs), `HOST` (PC runtime/CLI), `GUI_QT` (cửa sổ PySide6 thật), `PIO_BUILD` (firmware compile), `DEVICE` (ESP32-S3 thật có bằng chứng). Gate không chạy không chứng minh tier tương ứng.
- **Kết quả hợp lệ**: `PASS`, `FAIL`, `SKIPPED`, `NOT_RUN`. Nếu điều kiện chặn chưa đáp ứng, ghi `NOT_RUN + blocker`, không để trống hoặc nâng thành PASS. `SKIPPED` phải là trạng thái từ runner hoặc lý do bỏ qua được reviewer chấp nhận, không đại diện cho PASS.
- **Bằng chứng tối thiểu của mỗi dòng**: timestamp+timezone, git/ZIP SHA baseline, lệnh chính xác, OS/toolchain, exit code, log và artifact khi có. Với số liệu hiệu năng: số mẫu, cấu hình, baseline và phương pháp đo.
- **Bắt buộc** là theo trigger, không có nghĩa chạy mọi test cho patch docs. Ghi `N/A` trong Task Brief cho ID không áp dụng; các dòng trong bản test run chỉ dùng 4 trạng thái ở trên.

## 2. Ma trận kiểm thử theo tầng

**Đây là kế hoạch kiểm thử, chưa điền kết quả.** Đường dẫn CLI cần xác nhận tồn tại theo checkout thật; một số bước cần board, key/tệp project mẫu và toolchain được cấp phép.

| ID | Khi nào kích hoạt | Tier | Thực thi / quan sát | Tiêu chí PASS | Bằng chứng cần lưu |
|---|---|---|---|---|---|
| `DOC01` | Thay đổi AI docs | STATIC | `python tools/validate_agent_docs.py` | Đường dẫn/liên kết/hợp đồng CLI hợp lệ, exit 0 | stdout + exit code |
| `DOC02` | Thay đổi tài liệu hoặc role | STATIC | Kiểm `AGENTS.md`, handoff, matrix, manifest; so `git diff --check` | Không thiếu role/đường dẫn/bảng nhiệm vụ; không dùng kết quả giả | log soát + diff |
| `PY01` | Sửa Python IDE/launcher/tool | STATIC | `python -m compileall -q studio tools` | exit 0, không lỗi cú pháp | console log |
| `CORE01` | Sửa Studio core | HOST | `python -m unittest discover -s studio/tests -v` | 0 fail/error; số skipped tách riêng | unittest output |
| `CORE02` | Sửa package/host engine/tool | HOST | `python -m unittest discover -s tests -v` | 0 fail/error; báo prerequisite thiếu | unittest output |
| `GUI01` | Sửa Qt editor, Explorer, preview | GUI_QT | Windows: `run_studio.bat --gui-check`; hoặc Qt offscreen probe | QWidget thực khởi tạo, paint và kiểm các pane thật, không crash | `gui-check*.json` + PNG Qt thực |
| `GUI02` | Thay đổi launcher tự nâng cấp | GUI_QT | Upgrade staging → Qt probe → activate → reopen Studio | Active env chạy GUI mới; fail env không active | Qt log, GUI probe JSON/PNG |
| `GUI03` | Thay đổi editor/unsaved state | GUI_QT | Tạo project tạm → edit → switch/close → Save/Discard/Cancel | Không mất dữ liệu; file/project không bị ghi ngoài ý muốn | GUI event log và file diff |
| `UP01` | Safe updater, pip/venv | HOST | `python -m unittest studio.tests.test_launcher_v074 -v` | staging+failure/rollback paths test PASS | stdout + exit code |
| `UP02` | Safe updater, pip/venv | HOST | Tạo env staging lỗi giả lập; kiểm rollback pointer và project hash | Env cũ còn nguyên, log lỗi, dữ liệu user nguyên | hash trước/sau, launcher log |
| `VM01` | Lua VM/callback/memory | HOST | `python tools/test_lua_beta_host.py` (cần runtime prereq) | 0 crash/hang, negative cases đúng | log VM + exit code |
| `VM02` | Lua graphics/input/preview | HOST | `python tools/qstudio.py lua-preview projects/lua-snake --frames 14 -o build/qa-snake.png` | PNG phát sinh từ VM thật, frame count/CRC nếu baseline có | PNG + run log + hash |
| `VM03` | FPS/timing/step/watchdog VM | HOST | Replay cố định ≥ 2 lượt, đo FPS và memory theo cùng cấu hình | Không sai replay, không crash/timeout, drift trong giới hạn task brief | bảng số liệu + raw timing |
| `APP01` | Thêm project mẫu | HOST | `python tools/qstudio.py validate <project>` | manifest/resources hợp lệ cho đúng type | stdout + project SHA |
| `APP02` | Thêm mẫu Lua | HOST | VM preview chạy toàn bộ menu, Back, state | Không runtime error; ảnh/state chứng minh từng màn | frame PNG + replay log |
| `PKG01` | Sửa signer/parser | HOST | unittest package + ký thử bằng khóa **tạm** | Gói hợp lệ verify với đúng khóa và đúng ID | gói test hash + stdout đã redact |
| `PKG02` | Sửa signer/parser/trust | HOST | Tamper bytes, key ID sai, truncated/oversized package | Bị từ chối; không đọc ngoài vùng/OOM/crash | negative-case logs |
| `PKG03` | Build mẫu stock QEAPP/2 | HOST | `qstudio.py build/inspect` với firmware+test keys thật sự phù hợp | `text/web` hợp lệ, inspect đối chiếu đúng key ID | package metadata + hash |
| `FW01` | Mọi thay đổi firmware | PIO_BUILD | `pio run -d <verified-firmware-root> -e <verified-env>` | Compiler/link exit 0, dung lượng trong hạn | build log + firmware hash |
| `FW02` | Chỉ sửa lõi/Back OS | STATIC | So danh sách SHA-256 của theme/icon/font/layout/renderer với **cùng baseline** | Tất cả visual files giữ nguyên byte | baseline/current SHA diff |
| `FW03` | Back hoặc state machine | HOST | Chạy host Back regression hiện có trong đúng checkout | `No` giữ state, `Yes` cleanup, double Back không đúp popup | binary/run log |
| `FW04` | Installer/theme/resource | HOST | Host installer/signature/rollback regression ở checkout đã xác minh | Invalid package bị từ chối; rollback không mất dữ liệu | test names + run log |
| `DEV01` | Back core / input / cài app | DEVICE | Nạp đúng binary; thu Serial 115200 + quay LCD; Back ×20 (No/Yes) | Popup, return flow đúng; không panic/reset, state No nguyên | serial raw + mốc thời gian + video |
| `DEV02` | Installer / theme | DEVICE | Cài/update/sai chữ ký/hủy giữa chừng/trở lại launcher | Không bootloop; gói cũ được bảo toàn theo design | video + serial + package hashes |
| `DEV03` | Hiệu năng/đồ họa game | DEVICE | FPS + frame/render time + heap/PSRAM trước/sau chơi/Back | Theo ngưỡng trong Task Brief, không sai màu/icon/tearing bất thường | raw metrics + LCD video + cấu hình |
| `DEV04` | Audio/I2S thay đổi hoặc game có SFX | DEVICE | Phát/pause/resume/exit trên loa thật | Âm thanh đúng sự kiện, không bị rớt kênh/crash/underrun ngoài ngưỡng | thu âm + serial + chuỗi phím |
| `SEC01` | Gói phát hành, cài đặt, release | STATIC | Rà ZIP/commit/log với `git diff --check` + scan path nhạy cảm | Không chứa PEM private, token hoặc generated secrets | scan summary + file list |
| `REL01` | Mọi bản bàn giao | STATIC | Kiểm handoff + matrix + artifacts + hash ZIP | Claim khớp tier; mọi hạn chế nêu rõ; link tồn tại | handoff hoàn chỉnh + hash |

## 3. Bộ gate tối thiểu theo scope

| Scope | Bắt buộc trước khi chấp nhận phạm vi tương ứng | Chỉ khẳng định thêm khi có điều kiện |
|---|---|---|
| `TESTS_DOCS` | DOC01, DOC02, REL01 | Không tuyên bố runtime hoặc board PASS |
| `STUDIO_GUI` | PY01, CORE01, GUI01, SEC01, REL01 | GUI02/GUI03 khi launcher/editor chạm; GUI thật Windows cần chạy trên Windows |
| `LUA_HOST_VM` | CORE02, VM01, VM02, SEC01, REL01 | VM03 khi sửa FPS/timing; không suy ra device |
| `APP_TEMPLATE` | APP01, CORE02, SEC01, REL01 | APP02 với Lua, PKG03 nếu build stock |
| `QEAPP2_STOCK` | CORE02, PKG01, PKG02, PKG03, SEC01, REL01 | DEV02 để xác nhận thiết bị nhận gói |
| `LUA_BETA` | VM01, VM02, FW01, SEC01, REL01 | DEV01–DEV04 theo chức năng khi xác nhận trên beta board |
| `FIRMWARE_CORE: BACK` | FW02, FW03, FW01, SEC01, REL01 | DEV01 để ghi “đã xác minh trên máy thật” |
| `FIRMWARE_CORE: installer/render/audio` | FW01, FW04 (nếu installer), SEC01, REL01 | DEV02/DEV03/DEV04 theo chức năng thực tế |

Nếu gate bắt buộc không có toolchain/board, **được bàn giao bản candidate** kèm `NOT_RUN` nhưng **không** được tự nâng trạng thái thành released/device verified. Reviewer quyết định cấp độ đạt (`ACCEPTED_HOST_ONLY`, `ACCEPTED_GUI_QT`, `ACCEPTED_PIO_BUILD`, `ACCEPTED_DEVICE`) từ chứng cứ, không dựa vào phiên bản tên file.

## 4. Bảng thực thi — sao chép cho mỗi lần QA

| Test ID | Scope / tier | Baseline SHA | Thời gian+timezone | Lệnh hoặc phương pháp | Trạng thái | Exit code / case counts | Log/ảnh/video/hash | Blocker hoặc issue |
|---|---|---|---|---|---|---|---|---|
| `DOC01` | `TESTS_DOCS / STATIC` | `<sha>` | `<ISO8601>` | `<exact command>` | `NOT_RUN` | `—` | `—` | `<nếu chưa chạy>` |
| `<ID cần kiểm>` | `<scope/tier>` | `<sha>` | `<ISO8601>` | `<exact command>` | `NOT_RUN` | `—` | `—` | `<nếu chưa chạy>` |

Chỉ khi thực hiện mới cập nhật trạng thái. Nếu test hồi quy chạy trên một baseline khác, dùng hàng riêng với baseline riêng. Ảnh concept/manual chỉ là minh họa, không được liệt kê làm bằng chứng Qt, LCD hoặc thiết bị.

## 5. Chốt báo cáo và phân biệt kết quả

**Tổng:** `PASS=<số đã chạy đạt>`, `FAIL=<số đã chạy không đạt>`, `SKIPPED=<số runner bỏ qua>`, `NOT_RUN=<số chưa chạy>`. Nêu rõ số lượng theo tier; không tạo tỷ lệ “đạt 100%” khi gate quan trọng không chạy. Dán bảng vào [`HANDOFF_TEMPLATE.md`](HANDOFF_TEMPLATE.md), ghi QA reviewer và hạn chế. Với DEVICE đo FPS/render/audio, bắt buộc có dữ liệu raw từ firmware + ảnh/video thiết bị; nếu thiếu kết luận **DEVICE NOT_RUN**.
