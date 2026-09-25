# Lua Hello (EXPERIMENTAL)
This is a standalone Lua app for the explicitly enabled `vqeaf_lua_beta` firmware
profile. It cannot run on stock VQEAF OS v2.4.2, which supports only web/text.
Build with `qstudio build --experimental-lua --firmware-root ... --sign-key ...`.
Sign only with a key whose PUBLIC part is pinned in your test firmware.
