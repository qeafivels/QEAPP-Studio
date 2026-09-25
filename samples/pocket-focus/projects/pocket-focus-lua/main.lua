-- Pocket Focus 1.0: fully interactive, self-contained Lua 5.4 host app.
-- Guest area 240x270; OS owns status rows 0..28 and bottom softkeys.
-- Supported API: engine.clear, rect, text; no files, audio, RTC or network.
local W_PRESETS = {15,25,45}
local B_PRESETS = {3,5,10}
local C={bg=0x1082, panel=0x18E4, panel2=0x2145, blue=0x351F,
         cyan=0x07FF, white=0xFFFF, muted=0xAD55, green=0x07E0,
         yellow=0xFFE0, red=0xF9C8, black=0x0861}
local page='home'
local menu=1
local settingsCursor=1
local focusIndex=2
local breakIndex=2
local autoBreak=true
local phase='work'
local remaining=25*60
local phaseSeconds=25*60
local elapsed=0
local running=false
local completed=0
local creditedSeconds=0
local confirmYes=false
local function clamp(n,lo,hi) return math.max(lo,math.min(hi,n)) end
local function resetTimer()
  phase='work';phaseSeconds=W_PRESETS[focusIndex]*60
  remaining=phaseSeconds;elapsed=0;running=false
end
local function beginWork()
  resetTimer();running=true;page='timer'
end
local function beginBreak()
  phase='break';phaseSeconds=B_PRESETS[breakIndex]*60
  remaining=phaseSeconds;elapsed=0;running=true;page='timer'
end
local function leaveTimer()
  resetTimer();page='home';menu=1
end
local function onPhaseComplete()
  if phase=='work' then
    completed=completed+1
    creditedSeconds=creditedSeconds+W_PRESETS[focusIndex]*60
    if autoBreak then beginBreak() else running=false;page='complete' end
  else
    resetTimer();page='complete'
  end
end
function on_key(key,pressed)
  if not pressed then return end
  if page=='confirm' then
    if key=='left' or key=='right' then confirmYes=not confirmYes
    elseif key=='option' then page='timer';running=true
    elseif key=='start' then
      if confirmYes then leaveTimer() else page='timer';running=true end
    end
    return
  end
  if page=='home' then
    if key=='up' then menu=(menu+2)%4+1
    elseif key=='down' then menu=menu%4+1
    elseif key=='option' then page='about'
    elseif key=='start' then
      if menu==1 then beginWork()
      elseif menu==2 then page='settings';settingsCursor=1
      elseif menu==3 then page='stats'
      else page='about' end
    end
  elseif page=='timer' then
    if key=='start' then running=not running
    elseif key=='option' then running=false;confirmYes=false;page='confirm' end
  elseif page=='settings' then
    if key=='up' then settingsCursor=(settingsCursor+1)%3+1
    elseif key=='down' then settingsCursor=settingsCursor%3+1
    elseif key=='left' or key=='right' or key=='start' then
      local dir=(key=='left') and -1 or 1
      if settingsCursor==1 then focusIndex=clamp(focusIndex+dir,1,#W_PRESETS)
      elseif settingsCursor==2 then breakIndex=clamp(breakIndex+dir,1,#B_PRESETS)
      else autoBreak=not autoBreak end
    elseif key=='option' then resetTimer();page='home' end
  elseif page=='stats' or page=='about' or page=='complete' then
    if key=='option' or key=='start' then page='home' end
  end
end
function on_update(dt)
  if page~='timer' or not running then return end
  -- Each update must remain bounded, even when the host lags or is paused.
  dt=clamp(dt or 0,0,0.1)
  remaining=math.max(0,remaining-dt)
  elapsed=math.min(phaseSeconds,elapsed+dt)
  if remaining<=0 then running=false;onPhaseComplete() end
end
local function text(x,y,s,c) engine.text(x,y,s,c or C.white) end
local function outline(x,y,w,h,c)
  engine.rect(x,y,w,1,c);engine.rect(x,y+h-1,w,1,c)
  engine.rect(x,y,1,h,c);engine.rect(x+w-1,y,1,h,c)
end
local function header(label)
  engine.rect(0,0,240,34,C.panel2)
  engine.rect(0,32,240,2,C.cyan)
  engine.rect(10,9,17,17,C.cyan)
  engine.rect(14,13,9,9,C.bg)
  text(34,14,'POCKET FOCUS',C.white)
  text(12,43,label,C.yellow)
end
local function foot(s)
  engine.rect(0,239,240,31,C.panel2)
  engine.rect(0,239,240,1,C.blue)
  text(9,250,s,C.white)
end
local function badge(x,y,label,value,color)
  engine.rect(x,y,100,37,C.panel)
  outline(x,y,100,37,C.blue)
  text(x+8,y+6,label,C.muted)
  text(x+8,y+20,value,color or C.cyan)
end
local function fmt(sec)
  local n=math.max(0,math.ceil(sec-0.00001))
  return string.format('%02d:%02d',math.floor(n/60),n%60)
end
local function drawHome()
  header('PERSONAL TIMER')
  engine.rect(12,64,216,55,C.panel)
  outline(12,64,216,55,C.blue)
  text(24,76,'WORK / BREAK',C.muted)
  text(24,94,string.format('%02d MIN / %02d MIN',W_PRESETS[focusIndex],B_PRESETS[breakIndex]),C.cyan)
  local items={'START FOCUS','SETTINGS','STATISTICS','ABOUT'}
  for i=1,4 do
    local y=127+(i-1)*26
    if i==menu then engine.rect(12,y,216,22,C.blue);text(20,y+8,items[i],C.black)
    else engine.rect(12,y,216,22,C.panel);text(20,y+8,items[i],C.white) end
  end
  foot('UP DOWN / START OPEN')
end
local function drawTimer()
  header(phase=='work' and 'FOCUS IN PROGRESS' or 'TIME FOR A BREAK')
  local c=phase=='work' and C.cyan or C.green
  engine.rect(13,65,214,91,C.panel)
  outline(13,65,214,91,c)
  text(27,80,phase=='work' and 'WORK SESSION' or 'REST SESSION',C.muted)
  -- Chunked progress needs 20 small rectangles; no framebuffer or per-tick alloc.
  local chunks=math.floor(clamp(elapsed/phaseSeconds,0,1)*20+0.001)
  for i=1,20 do engine.rect(19+(i-1)*10,137,8,6,i<=chunks and c or C.panel2) end
  text(73,101,fmt(remaining),C.white)
  badge(13,168,'DONE',string.format('%03d',completed),C.green)
  badge(127,168,'MODE',running and 'RUNNING' or 'PAUSED',c)
  text(23,213,running and 'KEEP THE FLOW' or 'TAKE YOUR TIME',C.yellow)
  foot('START PAUSE / OPTION END')
end
local function drawSettings()
  header('SETTINGS')
  local items={
    'WORK  '..W_PRESETS[focusIndex]..' MIN',
    'BREAK '..B_PRESETS[breakIndex]..' MIN',
    'AUTO  '..(autoBreak and 'ON' or 'OFF')
  }
  text(15,69,'LEFT / RIGHT TO CHANGE',C.muted)
  for i=1,3 do
    local y=96+(i-1)*39
    engine.rect(12,y,216,30,settingsCursor==i and C.blue or C.panel)
    text(23,y+12,items[i],settingsCursor==i and C.black or C.white)
  end
  foot('OPTION BACK / START SET')
end
local function drawStats()
  header('SESSION STATISTICS')
  badge(13,77,'DONE',string.format('%03d',completed),C.green)
  badge(127,77,'FOCUS MIN',string.format('%04d',math.floor(creditedSeconds/60)),C.cyan)
  engine.rect(13,136,214,75,C.panel)
  outline(13,136,214,75,C.blue)
  text(22,154,'STATS ARE SESSION ONLY',C.yellow)
  text(22,181,'NO STORAGE API YET',C.muted)
  foot('OPTION / START BACK')
end
local function drawAbout()
  header('ABOUT THIS APP')
  engine.rect(12,69,216,140,C.panel)
  outline(12,69,216,140,C.blue)
  text(22,85,'POCKET FOCUS V1',C.cyan)
  text(22,107,'BUILT FOR QEAPP STUDIO',C.white)
  text(22,129,'LUA 5 / RGB565',C.muted)
  text(22,151,'WORK AND BREAK TIMER',C.white)
  text(22,173,'RETRO LAUNCHER STYLE',C.yellow)
  foot('OPTION / START BACK')
end
local function drawConfirm()
  drawTimer()
  -- The guest confirmation is ONLY for ending the timer. The physical
  -- BACK/HOME key is owned by the OS, which shows its own unmodified dialog.
  engine.rect(12,79,216,116,C.black)
  outline(12,79,216,116,C.yellow)
  text(35,96,'END CURRENT TIMER?',C.yellow)
  text(42,124,'PROGRESS WILL RESET',C.white)
  engine.rect(24,155,87,25,confirmYes and C.blue or C.panel2)
  engine.rect(129,155,87,25,not confirmYes and C.blue or C.panel2)
  text(52,164,'YES',confirmYes and C.black or C.white)
  text(159,164,'NO',not confirmYes and C.black or C.white)
  foot('LEFT RIGHT / START OK')
end
function on_draw()
  engine.clear(C.bg)
  if page=='home' then drawHome()
  elseif page=='timer' then drawTimer()
  elseif page=='settings' then drawSettings()
  elseif page=='stats' then drawStats()
  elseif page=='about' then drawAbout()
  elseif page=='confirm' then drawConfirm()
  elseif page=='complete' then
    header('SESSION COMPLETE')
    engine.rect(12,70,216,125,C.panel)
    outline(12,70,216,125,C.green)
    text(30,92,'NICE WORK',C.yellow)
    text(30,124,'FINISHED SESSIONS',C.muted)
    text(30,152,string.format('%03d',completed),C.green)
    foot('START FOR HOME')
  end
end
