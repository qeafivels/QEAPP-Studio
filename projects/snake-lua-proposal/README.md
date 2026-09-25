# Snake Lua prototype (unbuildable intentionally)

This project uses the proposed `qe.*` lifecycle. VQEAF OS 2.4.2 does not include a Lua engine nor accept `type=lua`. `qstudio validate` rejects this project with a clear runtime-not-implemented diagnostic. For a game playable **now**, use firmware's built-in `snake_pixel` signed-config handler and `games/pixel_snake/build_package.py` in VQEAF-OS.
