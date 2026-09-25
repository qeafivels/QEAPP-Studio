# QEAPP-Studio — Verified project layout for AI Agents

**Inspected baseline:** `QEAPP_Studio_v0.7.4_Safe_GUI_Update_Full_Source.zip` (Studio v0.7.4). This is a *readable selection* of existing code, not a request to move folders or rename source. `firmware/VQEAF-OS/` is a historical reference only; current firmware lives in the separate VQEAF-OS repository.

```text
QEAPP-Studio/
├── PROMPT.md / SKILLS.md / AGENTS.md      # AI master rules and discoverable entry
├── agents/                                # NEW: specialist role instructions
│   ├── README.md
│   ├── orchestrator.md
│   ├── studio-gui.md
│   ├── lua-runtime.md
│   ├── app-template.md
│   ├── package-security.md
│   ├── firmware-core.md
│   └── qa-release.md
├── docs/
│   ├── 02_PACKAGE_CONTRACT.md             # existing stock signed QEAPP/2 contract
│   ├── 10_LUA_BETA_ARCHITECTURE.md         # existing beta Lua limits
│   ├── 17_SAFE_GUI_UPDATES_v074.md         # existing safe staging & rollback
│   └── agents/                            # NEW: structure, tests & handoff templates
├── run_studio.bat / run_studio.py          # existing Windows / Python entry
├── requirements-studio.txt                # existing desktop dependencies
├── studio/
│   ├── main.py                             # Qt bootstrap
│   ├── gui/{window,code_editor,theme,virtual_phone}.py
│   ├── core/{workspace,jobs,commands,config,diagnostics,repair,...}.py
│   └── tests/test_*.py
├── engine/                                 # existing native host C++ engine
│   ├── include/qe/runtime.h
│   ├── src/{runtime,draw}.cpp
│   └── host/HostCanvas.cpp
├── runtime/
│   ├── include/QeLuaRuntime.h
│   ├── src/QeLuaRuntime.cpp
│   └── host/qe_lua_host.cpp
├── tools/
│   ├── qstudio.py                          # CLI: init,validate,doctor,build,inspect,test,preview
│   ├── studio_launcher.py                  # safe dependency updates
│   ├── safe_runtime_update.py
│   ├── gui_post_update_check.py
│   ├── bootstrap_lua.py / build_lua_host.py
│   └── validate_agent_docs.py              # NEW: docs integrity check
├── projects/
│   ├── text-notes/                         # stock QEAPP/2
│   ├── web-bookmark/                       # stock QEAPP/2
│   ├── lua-hello/                          # PC preview / beta only
│   ├── lua-snake/                          # PC preview / beta only
│   └── lua-sprite/                         # PC preview / beta only
├── (no firmware copied into this standalone repository)
└── tests/                                  # host/native/format/security regression
```

## Per-project layout and supported JSON schema

Existing `tools/qstudio.py init` generates from `projects/*`; prefer it over cloning unknown templates.

```text
my-lua-beta-app/
├── qeapp.project.json
├── main.lua
├── assets/icon.png          # OPTIONAL 32×32 PNG, only if JSON `icon` points to it
├── tests/input_replay.json  # OPTIONAL deterministic host replay
├── README.md                # recommended
└── CHANGELOG.md             # recommended
```

Valid Lua project metadata (desktop only):

```json
{
  "project_format": 1,
  "id": "my_lua_app",
  "name": "My Lua App",
  "version": "0.1.0",
  "type": "lua",
  "content": "main.lua"
}
```

For stock text app replace `type` with `text` and `content` with `content.txt`; for stock web app set `type=web` and `url=https://...`, without `content`. JSON metadata is never packed verbatim as QEAPP binary manifest. Generated `build/`, `dist/`, `.venv/`, `.qeapp_envs/`, `logs/`, private key paths should be excluded from commits.

## Real CLI entry points

```sh
python tools/qstudio.py --help
python tools/qstudio.py init --template lua-snake --id my_snake --name "My Snake" -o projects/my-snake
python tools/qstudio.py validate projects/my-snake
python tools/qstudio.py lua-preview projects/my-snake --frames 14 --replay tests/input_replay.json -o build/my-snake.png
python -m unittest discover -s studio/tests -v
python tools/validate_agent_docs.py
```

Host preview requires Lua upstream + host compilation. Publishing `.qeapp` requires signer, a private key owned by the publisher and matching firmware public key; device installation is another gate. A release ZIP can include full source and project templates without shipping private signing material.

## Boundaries and integration notes

- `studio/` GUI never independently implements the packer; use `tools/qstudio.py`.
- `runtime/` is Lua 5.4 beta/host; `engine/` is a separate native C++ host prototype.
- Firmware is a separate checkout. Set `QEAPP_FIRMWARE_ROOT`, verify its target commit and never overwrite OS sources during Studio-only tasks.
- Preserve existing VQEAF Retro-Go visual assets when the change request only targets core/Back.
- `AGENTS.md`/`agents/`/`docs/agents/` are documentation addition only; do not treat them as runtime features.
