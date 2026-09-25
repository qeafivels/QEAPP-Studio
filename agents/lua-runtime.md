# Role: Lua Runtime & Host VM

**Own:** `runtime/`, `studio/core/frame_protocol.py`, `tools/build_lua_host.py`, `tools/lua_preview.py`, host regression. Coordinate `virtual_phone.py` with GUI owner.

**API boundary:** `QeLuaRuntime` (start/update/render/key/stop), allowed Lua globals and callbacks only. Guard heap, source length, callback instruction/deadline and draw primitives. Preserve host protocol frame size and RGB565 little-endian. Do not implement new user-facing API without runtime bridge, tests, documentation and firmware beta plan.

**Gates:** build bounded PC VM with verified Lua upstream; run `tools/test_lua_beta_host.py`, test deterministic replay of `projects/lua-snake`, compare PNG/hash and record host frame timings. Test malformed source and interrupted guest; never treat host result as device or audio hardware evidence.

**Handoff:** changes in host and firmware mirror (if any), numeric budgets, suite output, screenshot provenance, compatibility limits.
