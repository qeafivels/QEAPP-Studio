# Sprite Ship (Lua beta QEAPP)

Portable 16×16 pixel-art mask, RGB565 colour, 240×270 Lua app canvas.
Press left/right or Start in a 3–8 frame host replay. This is a Lua project, not a prebuilt signed package.

```sh
python tools/build_lua_host.py --system-lua
python tools/lua_preview.py projects/lua-sprite/main.lua --frames 8 -o build/sprite_ship.png
```

Firmware target is experimental `vqeaf_lua_beta` only. To install, build with a private key matching the device beta public key; run platform target and device tests before release.
