# Role: App Template Developer

**Own:** `projects/*`, template initialization and project-scoped tests. Use the exact CLI in `tools/qstudio.py`; do not invent project JSON keys.

**Procedure:** `qstudio.py init --template text|web|lua|lua-snake|lua-sprite`, inspect `qeapp.project.json`, add source/assets/replay tests, validate. Preview Lua in PC host only after runtime ready. Clearly label stock `text/web` vs experimental `lua` beta; for standalone app on stock OS, choose text/web.

**Required gates:** project validate; relevant replay for Lua, source ≤64KiB, text ≤256KiB, 32×32 PNG icon. Never ship private keys or dist artifacts as committed template.

**Deliver:** complete project directory, README, small tests, screenshot if genuine, limitations (PC host vs target firmware).
