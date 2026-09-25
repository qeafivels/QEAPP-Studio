# Hợp đồng dữ liệu `.qeapp`: thực tế vs dự thảo runtime mới

## QEAPP/2 trong VQEAF OS v2.4.2 — PHẢI giữ nguyên

`QEAPP/2` là **binary signed file**; không phải ZIP/directory. Toàn bộ số nguyên little-endian:

```text
HEADER [116 bytes]
  magic[8]     = "QEAPP2\\r\\n" (bytes ASCII, CR LF thật)
  manifest_len = u32 LE (1..2048)
  icon_len     = u32 LE (0 hoặc 2048)
  payload_len  = u32 LE (0..262144)
  manifest_sha = SHA-256(manifest)[32]
  icon_sha     = SHA-256(icon)[32]; hash rỗng nếu không có icon
  payload_sha  = SHA-256(payload)[32]; hash rỗng nếu không có payload
CONTENT
  manifest[manifest_len] || icon[icon_len] || payload[payload_len]
TRAILER [76 bytes]
  "QSIGP256"[8] || key_id[u32 LE] || r[32 BE] || s[32 BE]
SIGNED_DIGEST = SHA256(header + manifest + icon + payload)
```

Chữ ký là ECDSA P-256 SHA-256; firmware ghim **một** public key/key-id ở `src/services/QeappTrustKey.h`. Demo Snake dùng key demo khác và môi trường firmware demo riêng; không đánh lừa người dùng bằng "đổi key-id" trên CLI nếu không có private key tương ứng.

Manifest ASCII dạng `key=value`, mỗi dòng LF. Whitelist thực của parser: `id`, `name`, `version`, `type`, và `entry` **chỉ** cho `web`. `id`: `[a-z0-9_-]{1,24}`; `name`: 1..40 printable ASCII; `version`: số có dấu chấm, tối đa 19 ký tự; `type=web|text`. Web: `entry=https://...`, payload rỗng. Text: KHÔNG có `entry`, có payload text không rỗng (builder kiểm soát; parser kiểm tra kích cỡ). Icon nếu có là 32x32xRGB565 little-endian **2048 bytes**, không phải PNG thô.

Ví dụ manifest (nằm *bên trong file*, không lưu là `manifest.json`):

```ini
id=text_notes
name=Text Notes
version=1.0.0
type=text
```

```ini
id=web_bookmark
name=Web Bookmark
version=1.0.0
type=web
entry=https://qeafivels.com/
```

**Giới hạn cài đặt:** Catalog hiện tại hiển thị tối đa 12 signed apps. Data service có ba slot `prefs.bin`, `state.bin`, `draft.bin`, 16KiB mỗi slot và tổng 32KiB/app; web/text chưa có API truy cập trực tiếp. Update tăng version bằng cùng key; không tự xóa data. Copy an toàn bằng staging/backup, tuy nhiên FAT không hoàn toàn atomic khi mất nguồn.

## Khi phát triển script engine: quyết định format trước khi code

Đừng đổi `type=lua` vào QEAPP/2 và gọi đó là tương thích. Hai hướng thiết kế cần ADR (Architecture Decision Record):

1. **QEAPP/3 (đề xuất):** versioned header/manifest mới, ký toàn bộ package, asset index có đường dẫn normalize, metadata permissions, engine API min version; viết parser/verifier/installer migration, giới hạn và fuzz mới. Firmware cũ từ chối có giải thích.
2. **Script trong signed `text` với handler C++ riêng**: chỉ dành cho demo đóng sẵn tương tự Snake, không có khả năng chạy game/app tùy ý và không được quảng bá như IDE tổng quát.

Nếu dùng hướng QEAPP/3, đây mới là **phác thảo**, chưa có magic cố định hoặc CLI build thật:

```yaml
# Ý tưởng manifest Studio, KHÔNG phải header binary QEAPP/3 chính thức
id: pixel_adventure
version: 0.1.0
engine: qe-lua
engine_api: 0.1
entry: src/main.lua
permissions: [storage.appdata]
assets: [assets/sprites.rle, assets/sfx.qsnd]
```

Quyết định định dạng phải bao gồm spec endian/byte offsets, nội dung chữ ký, size/recursion limits, entry validation, dependency handling, downgrade policy, keys/rotation, recovery after power loss và upgrade from web/text. Chỉ khi `docs/ADR-QEAPP3.md` được review mới code runtime và packer.

## Quy trình dùng khóa ký

Khóa riêng P-256: tạo 1 lần ngoài Git, backup offline; public key được ghim trong firmware. Mã mẫu công khai hoặc khóa của người khác sẽ không ký được app phù hợp firmware. Test signing sử dụng temporary key trong thư mục tạm không push vào repo. Trên board, installer vẫn phải verify trước và sau khi copy.
