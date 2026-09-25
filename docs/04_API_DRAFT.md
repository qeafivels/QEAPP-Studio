# Dự thảo API `qe.*` cho game/app Lua — CHƯA IMPLEMENT

**Không gọi trực tiếp những API trong file này trên firmware v2.4.2.** Đây là hợp đồng định hướng để triển khai sau khi QEAPP/3 và sandbox có ADR được duyệt. Firmware hiện chỉ hỗ trợ web/text và Snake native handler.

## Vòng đời (đề xuất)

```lua
function qe.init(ctx) end                     -- Khởi tạo một lần, ctx chỉ chứa capabilities đã cấp
function qe.update(dt_ms) end                 -- fixed-step; không gọi blocking I/O
function qe.draw(gfx) end                     -- batched RGB565, clip tự động
function qe.keypressed(key) end               -- key id lowercase
function qe.keyreleased(key) end
function qe.pause() end                       -- khi mất focus / HOME
function qe.resume() end
function qe.shutdown(reason) end              -- release resource theo hạn mức
```

Input logic dùng tên trừu tượng `up`,`down`,`left`,`right`,`ok`,`back`,`delete`,`option`; `menu` phải luôn dành cho OS. Mọi alias/numeric/T9 phải thuộc lớp dịch input của VQEAF và được test riêng; **không** sao chép tên phím LuaS30 vì mapping thiết bị khác. `select` long >600ms do OS xử lý.

Gfx dự kiến `gfx:clear(rgb565)`, `gfx:pixel(x,y,c)`, `gfx:fillRect(x,y,w,h,c)`, `gfx:sprite(asset_id,x,y)`, `gfx:text(x,y,s,color,font_id)`, `gfx:clip(rect)`, `gfx:present()`. Cần vẽ trong viewport app không ghi đè statusbar và softkey OS; coordinate origin của viewport phải được cố định trong SDK sau khi thiết kế.

App data dự kiến `ctx.storage:save(slot, bytes)` và `ctx.storage:load(slot)` với slot enum `prefs`, `state`, `draft`, giới hạn 16KiB mỗi slot, 32KiB tổng. Không có `open("/sd/...", ...)` và không có đường dẫn tự chọn. Audio dự kiến `ctx.audio:play(asset_id)` khi adapter backend tồn tại; WiFi chỉ qua `ctx.net` được cấp quyền và HTTPS certificate validation.

### Phác thảo game

File `projects/snake-lua-proposal/main.lua` minh họa logic và vòng đời **chưa có runtime**. Unit test game core nên viết chạy cả host và device; không đóng gói nó thành app `text` để giả mạo tính năng Lua.

## Engine C ABI đề xuất

`engine/include/qeapp_engine_api_draft.h` là header không được import vào firmware v2.4.2. Mọi hàm cần `api_version`, `app_id` đã verify, preallocated framebuffer (hoặc draw callback), `ticks_ms`, giới hạn heap/script budget và callback báo lỗi. Tất cả tài nguyên do engine sở hữu, giải phóng khi `shutdown`/crash. Đo hợp đồng real-time trên board thay vì chọn FPS tùy tiện.
