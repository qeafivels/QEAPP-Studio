-- Pocket Calculator 1.0 - QEAPP Studio v0.7.4 example.
-- Fully offline interactive Lua 5.4 PC host sample for 240x270 guest region.
-- OS owns MENU/BACK/SELECT and renders its existing chrome/dialogs.
-- engine API intentionally limited to clear/rect/text in RGB565.
local C={bg=0x0861, panel=0x1924, panel2=0x29A6, accent=0x34FF,
         cyan=0x07FF, white=0xFFFF, muted=0x9CF3, yellow=0xFFE0,
         red=0xF9C8, green=0x07E0, black=0x0020}
local page='home'
local previous='home'
local menu=1
local homeItems={'CALCULATOR','HISTORY','ABOUT'}
local buttons={{'7','8','9','/'},{'4','5','6','*'},
               {'1','2','3','-'},{'C','0','.','+'},
               {'+/-','DEL','=','HIST'}}
local row,col=1,1
local entry='0'
local pending=nil
local stored=nil
local waiting=false
local errorMessage=nil
local history={}
local historyIndex=1
local showHelp=true
local function txt(x,y,s,color) engine.text(x,y,tostring(s),color or C.white) end
local function border(x,y,w,h,color)
  engine.rect(x,y,w,1,color);engine.rect(x,y+h-1,w,1,color)
  engine.rect(x,y,1,h,color);engine.rect(x+w-1,y,1,h,color)
end
local function clearAll()
  entry='0';stored=nil;pending=nil;waiting=false;errorMessage=nil
end
local function formatNumber(n)
  if n~=n or n==math.huge or n==-math.huge or math.abs(n)>1e10 then return nil end
  if n==0 then return '0' end
  local s=string.format('%.8g',n)
  return s
end
local function addHistory(s)
  if #history>=5 then table.remove(history,1) end
  history[#history+1]=s
  historyIndex=#history
end
local function digit(s)
  if errorMessage then clearAll() end
  if waiting then entry='0';waiting=false end
  if s=='.' then
    if not string.find(entry,'.',1,true) then entry=entry..'.' end
    return
  end
  local len=#entry
  if string.sub(entry,1,1)=='-' then len=len-1 end
  if len>=10 then return end
  if entry=='0' then entry=s
  elseif entry=='-0' then entry='-'..s
  else entry=entry..s end
end
local function compute(left,op,right)
  if op=='+' then return left+right end
  if op=='-' then return left-right end
  if op=='*' then return left*right end
  if op=='/' then
    if right==0 then return nil,'DIVIDE BY ZERO' end
    return left/right
  end
  return right
end
local function operate(op)
  if errorMessage then return end
  local number=tonumber(entry) or 0
  if pending and not waiting then
    local left=stored or 0
    local value,err=compute(left,pending,number)
    local formatted=value and formatNumber(value)
    if not formatted then
      entry='0';pending=nil;stored=nil;waiting=true
      errorMessage=err or 'RESULT TOO LARGE';return
    end
    local expression=formatNumber(left)..' '..pending..' '..formatNumber(number)..' = '..formatted
    entry=formatted
    stored=value
    if op=='=' then addHistory(expression) end
  else
    stored=number
  end
  if op=='=' then pending=nil;stored=nil
  else pending=op end
  waiting=true
end
local function pressButton(s)
  if s=='C' then clearAll();return end
  if s=='HIST' then previous='calculator';page='history';historyIndex=#history>0 and #history or 1;return end
  if s=='DEL' then
    if errorMessage then clearAll();return end
    if waiting then return end
    if #entry<=1 or (#entry==2 and string.sub(entry,1,1)=='-') then entry='0'
    else entry=string.sub(entry,1,-2) end
    return
  end
  if s=='+/-' then
    if errorMessage then clearAll();return end
    if entry=='0' then return end
    if string.sub(entry,1,1)=='-' then entry=string.sub(entry,2)
    else entry='-'..entry end
    return
  end
  if s=='+' or s=='-' or s=='*' or s=='/' or s=='=' then operate(s);return end
  digit(s)
end
function on_key(key,down)
  if not down then return end
  if page=='home' then
    if key=='up' then menu=(menu+1)%3+1
    elseif key=='down' then menu=menu%3+1
    elseif key=='start' then
      if menu==1 then page='calculator';row=1;col=1
      elseif menu==2 then previous='home';page='history'
      else page='about' end
    elseif key=='option' then page='about' end
  elseif page=='calculator' then
    if key=='up' then row=(row+3)%5+1
    elseif key=='down' then row=row%5+1
    elseif key=='left' then col=(col+2)%4+1
    elseif key=='right' then col=col%4+1
    elseif key=='start' then pressButton(buttons[row][col])
    elseif key=='option' then page='home' end
  elseif page=='history' then
    if key=='up' then historyIndex=math.max(1,historyIndex-1)
    elseif key=='down' then historyIndex=math.min(#history,historyIndex+1)
    elseif key=='start' then
      -- Reuse result of a prior operation as the next expression.
      if #history>0 then
        local value=string.match(history[historyIndex],'= ([^ ]+)$')
        if value and tonumber(value) then
          entry=value;waiting=true;pending=nil;stored=nil;errorMessage=nil
          page='calculator'
        end
      end
    elseif key=='option' then page=previous end
  elseif page=='about' then
    if key=='start' or key=='option' then page='home' end
  end
end
function on_update(dt)
  -- Intentional no-op: all arithmetic and drawing are event-driven.
  -- No VM file, audio, time or network API is assumed.
end
local function header(title)
  engine.rect(0,0,240,30,C.panel2)
  engine.rect(0,29,240,2,C.cyan)
  txt(10,9,'POCKET CALC',C.white)
  txt(10,39,title,C.yellow)
end
local function footer(s)
  engine.rect(0,243,240,27,C.panel2)
  engine.rect(0,243,240,1,C.accent)
  txt(8,253,s,C.white)
end
local function drawHome()
  header('TOOLS / OFFLINE')
  engine.rect(12,62,216,56,C.panel)
  border(12,62,216,56,C.accent)
  txt(23,75,'A TINY RGB565 DEMO',C.cyan)
  txt(23,94,'NO NETWORK NEEDED',C.muted)
  for i=1,3 do
    local y=129+(i-1)*31
    engine.rect(12,y,216,25,i==menu and C.accent or C.panel)
    txt(22,y+9,homeItems[i],i==menu and C.black or C.white)
  end
  footer('UP DOWN / START OPEN')
end
local function drawCalc()
  header('ARROW KEYS + START')
  engine.rect(9,57,222,53,C.panel)
  border(9,57,222,53,errorMessage and C.red or C.accent)
  local top=errorMessage or (stored and (formatNumber(stored)..' '..(pending or '')) or 'READY')
  txt(17,64,top,errorMessage and C.red or C.muted)
  local value=entry
  if #value>15 then value=string.sub(value,1,15) end
  txt(17,85,value,C.white)
  for i=1,5 do
    for j=1,4 do
      local x,y=9+(j-1)*56,116+(i-1)*25
      local selected=i==row and j==col
      local label=buttons[i][j]
      local bg=C.panel
      if selected then bg=C.accent
      elseif label=='=' then bg=C.green
      elseif label=='C' then bg=C.red end
      engine.rect(x,y,51,21,bg)
      txt(x+(label=='HIST' and 9 or 13),y+7,label,selected and C.black or C.white)
    end
  end
  footer('START TAP / OPTION HOME')
end
local function drawHistory()
  header('LAST 5 RESULTS')
  if #history==0 then
    engine.rect(12,82,216,80,C.panel)
    border(12,82,216,80,C.accent)
    txt(23,106,'NO SAVED RESULTS',C.muted)
    txt(23,132,'TRY THE CALCULATOR',C.white)
  else
    txt(12,64,'SELECT RESULT TO REUSE',C.muted)
    for i=1,#history do
      local y=86+(i-1)*29
      local highlighted=i==historyIndex
      engine.rect(8,y,224,25,highlighted and C.accent or C.panel)
      txt(13,y+9,history[i],highlighted and C.black or C.white)
    end
  end
  footer('START REUSE / OPTION BACK')
end
local function drawAbout()
  header('ABOUT')
  engine.rect(12,70,216,148,C.panel)
  border(12,70,216,148,C.accent)
  txt(23,84,'POCKET CALCULATOR V1',C.cyan)
  txt(23,107,'LUA 5.4 / 240X270',C.white)
  txt(23,130,'5 OPERATION HISTORY',C.white)
  txt(23,153,'RGB565 / D-PAD INPUT',C.muted)
  txt(23,176,'SESSION MEMORY ONLY',C.yellow)
  txt(23,197,'NO SYSTEM KEY OVERRIDE',C.muted)
  footer('OPTION / START BACK')
end
function on_draw()
  engine.clear(C.bg)
  if page=='home' then drawHome()
  elseif page=='calculator' then drawCalc()
  elseif page=='history' then drawHistory()
  else drawAbout() end
end
