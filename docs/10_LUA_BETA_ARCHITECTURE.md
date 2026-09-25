# M3–M4: Lua 5.4 beta runtime + firmware adapter

## Hợp đồng đã code

- **Engine interface:** `QeLuaRuntime` với `start(source,len,Draw,heapLimit)`, `update(dt)`, `render()`, `key(name,pressed)`, `stop()`; cùng source C++ ở `runtime/src` và bản mirror feature-gated trong `firmware/VQEAF-OS/src/lua/`.
- **Lua-facing API** hiện có: `engine.clear(rgb565)`, `engine.rect(x,y,w,h,rgb565)`, `engine.text(x,y,string,rgb565)`, `engine.width=240`, `engine.height=270`. 29 px header + 21 px footer do host compositor dùng là **mô phỏng**, không phải ABI framebuffer ngoài.
- **Script callbacks:** `on_update(dt)`, `on_draw()`, `on_key(key,down)`. Cặp key event; không phỏng đoán phím giữ. Accepted keys: `up/down/left/right/start/option`; các phím dành cho OS (`MENU`, `A/Back`, `B/Delete`, `SELECT long`) KHÔNG cấp cho Lua.
- **VM restrictions:** source text ≤64KiB; heap VM 16KiB–1MiB (beta device 192KiB), callback 75.000 Lua VM instructions và khoảng 65ms deadline; tối đa 512 primitive draw trong mỗi callback. Các thư viện chỉ `_G`, `math`, `string`, `table`, `utf8`. `os/io/package/debug/require/dofile/load` không được cung cấp; `string.dump` bị loại bỏ. Biên dịch Lua bytecode không được chấp nhận.
- **Renderer:** kiểm tra màu RGB565 0..65535; clipping bảo vệ tràn số 32-bit trước khi chuyển dữ liệu sang TFT; bỏ qua text quá 48 bytes; `drawCalls` hard cap chặn đóng băng SPI.
- **Trust boundary:** firmware chỉ khởi chạy payload của app đã cài có chữ ký hợp lệ và type `lua`, không đọc script tự do từ SD. `vqeaf_lua_beta` yêu cầu provision riêng public P-256. Không ghi private key vào firmware/repo.

## Build target còn cần xác minh

`tools/bootstrap_lua.py` cần tải Lua upstream hoặc `--archive` và phải xác minh SHA256. Beta sử dụng 8MB PSRAM qua `heap_caps_malloc/realloc/free` và feature-flag `VQEAF_ENABLE_LUA`; profile stock không bật VM. Đã kiểm thử compile/link trên host với stub Arduino và thư viện Lua hệ thống, **chưa có kết quả PlatformIO thật**, chưa có đo FPS/heap/fragmentation hoặc trace watchdog trên ESP32-S3 N16R8.

## Các gate trước khi đưa lên thiết bị

1. Provision key beta vào `QeappTrustKeyLuaBeta.h` (bản template có `#error` theo chủ đích); không sửa key production.
2. Bootstrap official Lua 5.4.8, xác minh hash/license, build `pio run -d firmware/VQEAF-OS -e vqeaf_lua_beta` và đọc toàn bộ lỗi link/map.
3. Nạp đúng board mapping từ repo. Ghi log Serial 115200; xác minh FAT SD và installer không chấp nhận gói sửa đổi, gói signed sai key/type, oversized source.
4. Ghi heap trước/sau install, launch/exit/reboot 100 lần, soak game ≥10 phút, latency phím, 20 FPS budget, timeout điều kiện vô hạn; có recovery UI khi Lua lỗi, không reset watchdog.
5. Chỉ sau khi các gate này PASS mới gọi runtime đã kiểm chứng trên thiết bị. `type=lua` là **beta riêng**, không phải ABI QEAPP/2 ổn định chung.
