# QEAPP Studio và Game/App Engine — kiến trúc + roadmap

Mục tiêu: xây dựng môi trường PC tạo dự án, editor, import pixel assets, giả lập hành vi game/app, build, ký `.qeapp`, cài và debug trên VQEAF OS. Học *cách tổ chức* từ LuaS30-IDE, không lấy ABI MRE, media SDK hoặc file `.vxp`.

## Các tầng hệ thống

```text
[PySide6 IDE] project editor / sprite editor / log / profiler / AI panel
      | gọi CLI, không parse/ký lại ở UI
[Project model + linter + Asset compiler]   [secure signing service]
      |                                           |
[Host Engine + deterministic simulator]       [QEAPP packager]
      |   unit/integration + screenshots             |
      +----[engine API + capability contract]--------+
                         |
            [QEAPP runtime/installer integration]
              |              |             |
            [Graphics]     [Input]     [AppData/Audio]
             RGB565       Fixed keys       limited
                  [ESP32-S3 / VQEAF OS]
```

**Engine core portable** không import Arduino/TFT_eSPI trực tiếp. Adapter ESP32 ánh xạ GPIO/events và render qua VQEAF; adapter host dùng cùng vòng đời và mock resource/input/clock để test. GUI IDE độc lập với target, giống tính chất Studio/toolchain/engine separation của LuaS30-IDE.

## Milestones, tiêu chí dừng

| Mốc | Nội dung | Kết quả kiểm chứng |
|---|---|---|
| M0 — hiện có | Validate/build/inspect `web` & `text` bằng builder VQEAF gốc (kit này), quản lý project | Host P-256 roundtrip, tamper FAIL, project JSON chuẩn |
| M1 — host game core (**HOST PASS v0.2**) | C++ game loop fixed timestep, event queue, RGB565 host canvas 240x320, render clipping + PNG screenshot; ESP32 adapter chưa làm | 5 golden screenshots, deterministic test, 1.200 tick mô phỏng và event queue cap |
| M2 — IDE alpha | PySide6 Explorer/editor, New Project wizard, preview icon, build log, Build/Stop, simulator, serial console | Open/save/project migration, không chặn GUI khi build |
| M3 — runtime ADR | Thiết kế QEAPP/3 và capability/per-app data API, byte format/version/limits, threat model, approve design | Review ADR và tests parser malformed; không gọi script hỗ trợ trước đó |
| M4 — sandbox Lua | Đưa interpreter đã kiểm soát vào firmware, không dùng raw SD/ESP-IDF, hạn mức instruction/memory và lifecycle | Host/ESP32 equivalence, crash returns launcher, fuzz không OOM |
| M5 — app/game runtime | Stable `qe.*` SDK, asset pipeline RGB565/palette/RLE, sound API tùy phần cứng, save/load slot; event/key contract | 2 sample games + 1 app có chữ ký, E2E trên board |
| M6 — quality/release | SDK ABI compat, update/downgrade/power-loss recovery, startup benchmark, CI security, docs & template gallery | Real board 10-min soak, serial logs, independent reproducible signed build |

Không gộp "IDE đã chạy" với "runtime đã chạy". M0 trong kit có thể thực thi và test. M1 host C++ đã có trong kit v0.2; M2–M6 vẫn là công việc cần triển khai. M1 chưa được kiểm chứng trên thiết bị.

## Project layout người phát triển nhìn thấy

```text
MyGame/
├── qeapp.project.json            # Studio metadata PC-only
├── src/main.lua                  # Chỉ dành cho runtime M4+ (DRAFT)
├── assets/{sprites,audio,fonts}/
├── tests/{logic,render,input}/
├── docs/{DESIGN,CHANGELOG}.md
└── dist/                         # <id>.qeapp, report.json, checksums
```

LuaS30-IDE dùng engine hướng S30+; tại VQEAF runtime Lua phải tự viết bridge cho ESP32, không phụ thuộc thư viện MediaTek hoặc file `.vxp`. Game Snake hiện tại (`src/apps/PixelSnakeApp.*`) là **ví dụ native handler cụ thể**, chưa phải plugin/VM host đa ứng dụng.

## Phân công modules

- **IDE:** quản lý project JSON và tài sản, editor, asset palette, simulator controls, build queue, log, source locations, serial monitor; không lưu passphrase PEM.
- **CLI:** validate project, build assets, gọi signer đúng version, inspect hashes/signature, run host tests, xuất `dist/build-report.json`; cùng API được IDE/CI gọi.
- **Engine:** tick/input, sprite/tile draw RGB565, text, audio dispatcher, lifecycle/state serialization, resource cache; abstractions host/ESP32.
- **Runtime broker:** load signed package sau installer, kiểm capability, cấp context app-ID và watchdog; mọi service OS được bọc API theo quyền. Key public firmware không thay đổi tùy ý.
- **Platform ESP32:** tích hợp scheduler/UI/key dispatch; không cho game chặn Menu/Home hoặc phần mềm cập nhật firmware; dừng app khi panic thay vì reboot vô hạn.
