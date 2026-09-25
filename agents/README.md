# QEAPP-Studio AI Agent Roles

Each task has **one orchestrator**, one primary code owner and a QA reviewer. Work on isolated branches or separate file scopes. Never auto-merge changes to `studio/gui/window.py`, `tools/qstudio.py`, firmware `src/main.cpp` from two agents without conflict review.

| Agent | Owns | Reads | Must not claim |
|---|---|---|---|
| [`orchestrator.md`](orchestrator.md) | Scope, dependency, integration | `PROMPT.md`, handoff template | success without gate evidence |
| [`studio-gui.md`](studio-gui.md) | IDE, Windows launcher, Qt smoke | Studio GUI + safe updater | GUI verified when Qt skipped |
| [`lua-runtime.md`](lua-runtime.md) | Lua runtime / PC VM | `runtime/`, protocol/replay | PC host = real ESP32 |
| [`app-template.md`](app-template.md) | templates, project JSON, tests | `projects/`, qstudio | Lua beta is stock `.qeapp` |
| [`package-security.md`](package-security.md) | signed format, installer boundaries | firmware parser/signer | any PEM = trusted device |
| [`firmware-core.md`](firmware-core.md) | target firmware core/Back | actual selected firmware | changing Retro-Go visual in core-only patch |
| [`qa-release.md`](qa-release.md) | tests, logs, verification, release | test matrix | SKIP = PASS |

**Workflow:** orchestrator issues a small scoped task with baseline → primary agent implements/tests → QA reproduces and checks restricted files → orchestrator integrates and writes user-facing report. The latest VQEAF OS Back r2 source may be **external to v0.7.4 Studio ZIP**, so confirm input rather than replacing it with an older embedded version.
