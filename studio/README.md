# QEAPP Studio v0.7 · PySide6 UI and virtual phone

The desktop editor uses a four-area layout: vertical activity rail, Explorer
with file filtering, tabbed code editor plus lower output log, and an interactive
virtual phone pane. Action shortcuts: **Ctrl+O** open project, **Ctrl+P** open
project file, **Ctrl+B** hide Explorer, **Ctrl+F** find, **F6** validate,
**F7** signed package build, **F8** deterministic replay image, **F9** live
Lua host VM, **Shift+F5** stop. Qt window and splitter dimensions persist
in user-local QSettings; signing keys are NEVER saved.

The PC virtual phone executes bounded Lua 5.4 via QProcess using the same
`QeLuaRuntime.cpp` as the beta firmware port. Frames are streamed as 240×270
RGB565 and composed in the UI with 29/21 host-only system bars. This is **not**
an emulator of ESP32-S3 hardware, ST7789, firmware apps/themes, Symbian or MRE.

See `../docs/15_M3_PYSIDE6_VIRTUAL_PHONE.md` for build, keypad and verification.


## 0.7 bổ sung

- `Ctrl+Shift+F`: Search tất cả tệp source trong project (bao gồm editor chưa Save); double-click kết quả để nhảy đến dòng/cột.
- `Ctrl+H` Replace, `Ctrl+G` Go to Line, editor gutter hiện số dòng, bảng PROBLEMS dành cho job lỗi, `Ctrl+J` ẩn/hiện bottom panel.
- Máy ảo Lua 240×320 có Pause/Resume/Step và timer cap 15/30 FPS. Hiển thị FPS **host** đã vẽ, round-trip response, guest render trung bình 30 frame và Lua heap used/peak.
- `tools/verify_v07.py --require-qt` là gate bắt buộc trước khi xác nhận GUI. Báo cáo có `NOT_RUN` khi chưa kiểm tra Qt/board.

Thông tin chi tiết: `../docs/16_V07_WORKBENCH_AND_VIRTUAL_PHONE.md`.
