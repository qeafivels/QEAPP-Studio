-- ship: 16x16 1-bit sprite; row-major MSB-first; transparent zeros.
local ship_bits = "\x01\x80\x03\xC0\x07\xE0\x0D\xB0\x19\x98\x31\x8C\x7F\xFE\x6F\xF6\x67\xE6\x37\xEC\x3F\xFC\x1E\x78\x0E\x70\x06\x60\x02\x40\x02\x40"
local ship_w, ship_h = 16, 16
-- Draw inside on_draw():
-- engine.blit1(20, 20, ship_w, ship_h, ship_bits, 0xFFFF)

local x, y, vx, score = 112, 115, 48, 0
function on_key(k, pressed)
  if not pressed then return end
  if k == 'left' then x=math.max(0,x-4) end
  if k == 'right' then x=math.min(224,x+4) end
  if k == 'start' then score=score+1 end
end
function on_update(dt)
  if dt<0 then dt=0 end
  if dt>0.1 then dt=0.1 end
  y=y+vx*dt
  if y>170 then y=170;vx=-48 end
  if y<70 then y=70;vx=48 end
end
function on_draw()
  engine.clear(0x0841)
  engine.text(12,5,'SPRITE SHIP',0xffff)
  engine.text(14,248,'DPAD MOVE / START',0x07ff)
  engine.blit1(math.floor(x),math.floor(y),ship_w,ship_h,ship_bits,0xffe0)
end
