-- Standalone Lua game/app sample. Uses only the VQEAF engine API.
local player = { x=104, y=116 }
local shade = 0
function on_key(key, down)
  if not down then return end
  if key == 'left' then player.x = math.max(0, player.x - 8) end
  if key == 'right' then player.x = math.min(engine.width-16, player.x + 8) end
  if key == 'up' then player.y = math.max(0, player.y - 8) end
  if key == 'down' then player.y = math.min(engine.height-16, player.y + 8) end
  if key == 'start' then shade = (shade + 1) % 2 end
end
function on_update(dt)
  -- Deterministic update. No file/network/native OS APIs are exposed.
end
function on_draw()
  engine.clear(shade == 0 and 0x0924 or 0x2104)
  engine.text(12, 16, 'HELLO QEAPP LUA', 0xffff)
  engine.rect(player.x,player.y,16,16,0x07e0)
  engine.text(12, 245, 'DPAD move  /  B exit', 0xffff)
end
