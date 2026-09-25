-- VQEAF Snake: sample independent signed Lua application.
-- Max drawing area 240x270. Avoid whole-screen framebuffers and unbounded assets.
local W, H, C, X, Y = 18, 17, 12, 12, 24
local snake, direction, next_direction, apple, score = {}, 'right', 'right', {x=11,y=8}, 0
local state, elapsed, seed = 'ready', 0, 23
local opposite={left='right',right='left',up='down',down='up'}
local step={left={x=-1,y=0},right={x=1,y=0},up={x=0,y=-1},down={x=0,y=1}}
local function contains(x,y)
  for i=1,#snake do if snake[i].x==x and snake[i].y==y then return true end end
  return false
end
local function rand(n)
  seed=(seed*1103515245+12345)%2147483647
  return (seed%n)+1
end
local function reset()
  snake={{x=8,y=8},{x=7,y=8},{x=6,y=8}}
  direction,next_direction='right','right'
  apple={x=11,y=8}
  state,elapsed,score='ready',0,0
end
local function spawn()
  if #snake >= W*H then state='won'; return end
  for i=1,300 do
    local x,y=rand(W)-1,rand(H)-1
    if not contains(x,y) then apple={x=x,y=y};return end
  end
  -- Exactly bounded fallback if random positions become crowded.
  for y=0,H-1 do for x=0,W-1 do
    if not contains(x,y) then apple={x=x,y=y}; return end
  end end
  state='won'
end
local function advance()
  direction=next_direction
  local dx,dy=step[direction].x,step[direction].y
  local head={x=snake[1].x+dx,y=snake[1].y+dy}
  if head.x<0 or head.x>=W or head.y<0 or head.y>=H then state='gameover';return end
  local grows=head.x==apple.x and head.y==apple.y
  -- Tail cell is allowed when it is vacated on this very move.
  local check_count=grows and #snake or #snake-1
  for i=1,check_count do
    if head.x==snake[i].x and head.y==snake[i].y then state='gameover';return end
  end
  table.insert(snake,1,head)
  if grows then score=score+10;spawn() else table.remove(snake) end
end
function on_key(key,down)
  if not down then return end
  if key=='start' then
    if state=='ready' or state=='gameover' or state=='won' then
      if state~='ready' then reset() end
      state='playing'
    elseif state=='playing' then state='paused'
    elseif state=='paused' then state='playing' end
  elseif step[key] and key~=opposite[direction] then
    next_direction=key
  end
end
function on_update(dt)
  if state~='playing' then return end
  elapsed=elapsed+dt
  local interval=math.max(0.09,0.20-score/400)
  if elapsed>=interval then elapsed=elapsed-interval; advance() end
end
function on_draw()
  engine.clear(0x1082)
  engine.text(12,6,'PIXEL SNAKE',0xFFE0)
  engine.text(152,6,string.format('%04d',score),0xFFFF)
  engine.rect(10,22,220,206,0x07e0)
  engine.rect(11,23,218,204,0x0000)
  engine.rect(X+apple.x*C+1,Y+apple.y*C+1,10,10,0xF800)
  for i=#snake,1,-1 do
    local p=snake[i]
    engine.rect(X+p.x*C+1,Y+p.y*C+1,10,10,i==1 and 0xFFE0 or 0x07E0)
  end
  if state=='ready' then engine.text(16,239,'START = PLAY',0xFFFF)
  elseif state=='paused' then engine.text(16,239,'PAUSED / START',0xFFFF)
  elseif state=='gameover' then engine.text(16,239,'LOST / START AGAIN',0xFFFF)
  elseif state=='won' then engine.text(16,239,'WIN / START AGAIN',0xFFFF)
  else engine.text(16,239,'OPTION MENU / B EXIT',0xFFFF) end
end
reset()
