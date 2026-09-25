-- PROPOSAL ONLY! `qe.*` does not exist in firmware v2.4.2.
-- A future simulator and sandbox must implement + test these functions.
local x, y, dx, dy = 8, 8, 1, 0
local step = 0
function qe.init(ctx)
  x, y, dx, dy, step = 8, 8, 1, 0, 0
end
function qe.keypressed(k)
  if k == 'up' and dy == 0 then dx, dy = 0, -1 end
  if k == 'down' and dy == 0 then dx, dy = 0, 1 end
  if k == 'left' and dx == 0 then dx, dy = -1, 0 end
  if k == 'right' and dx == 0 then dx, dy = 1, 0 end
end
function qe.update(dt_ms)
  step = step + dt_ms
  if step >= 150 then
    step = step - 150
    x, y = (x + dx) % 16, (y + dy) % 18
  end
end
function qe.draw(gfx)
  gfx:clear(0x1c62)
  gfx:fillRect(24 + x*12, 60 + y*12, 12, 12, 0x07e0)
end
