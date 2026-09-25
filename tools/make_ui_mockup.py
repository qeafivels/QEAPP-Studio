#!/usr/bin/env python3
"""Create an explicitly labeled *illustrative concept*, never a Qt screenshot.
Embeds the genuine stream-captured Lua host frame in the conceptual device.
Requires Pillow and a PNG from virtual_phone_cli.py.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
FRAME=ROOT/'docs/images/LUA_VM_ACTUAL_FRAME.png'
OUTPUT=ROOT/'docs/images/UI_MOCKUP_v06.png'
W,H=1510,920
im=Image.new('RGB',(W,H),'#101322')
d=ImageDraw.Draw(im)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
monopath='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
fonts={k:ImageFont.truetype(fontpath,k) for k in [10,11,12,13,14,17,19,23]}
mono={k:ImageFont.truetype(monopath,k) for k in [10,11,12,13,14]}

# utility
def rect(box,fill,outline=None,r=0,width=1):
 if r:d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
 else:d.rectangle(box,fill=fill,outline=outline,width=width)
def text(x,y,value,c='#e6eaff',sz=12,m=False):d.text((x,y),value,font=(mono if m else fonts)[sz],fill=c)

rect((0,0,1510,36),'#141a2d')
text(18,9,'◆  QEAPP STUDIO', '#c1b8ff',14)
text(245,11,'File    Edit    View    Build / Run    Tools    Help', '#c5cde4',12)
text(1220,11,'v0.6   •   PC HOST VM', '#96deb0',11)
rect((0,36,55,892),'#161b30',outline='#2e3653')
for i,(icon,label) in enumerate([('◧','Explorer'),('⌕','Search'),('▦','Device'),('⚒','Build')]):
 yy=82+i*55
 if i==0:rect((2,yy-7,54,yy+37),'#2c3050');rect((2,yy-7,5,yy+37),'#ab9aff')
 text(12,yy,icon,'#b8b0fc' if i==0 else '#8f9bb8',23)

rect((56,36,288,892),'#161b30',outline='#303652')
text(70,57,'EXPLORER', '#d3d8ed',11)
rect((70,86,274,113),'#202740',r=5,outline='#3b4566')
text(82,94,'Filter project files...', '#8390b0',11)
text(72,135,'⌄  LUA-SNAKE', '#e5e9f9',12)
for i,(indent,title,col) in enumerate([
 (' ','⌄   assets','#b6bedc'),('   ','◧  snake.png','#bdd6ae'),
 (' ','⌄   tests','#b6bedc'),('   ','{} input_replay.json','#c6a6fb'),
 (' ','◎ main.lua','#b2d6fb'),(' ','{} qeapp.project.json','#c6a6fb'),
 (' ','▤ README.md','#adb8cf')]):
 y=164+i*32
 if 'main.lua' in title:rect((61,y-5,285,y+24),'#30335b');rect((61,y-5,64,y+24),'#a99bfa')
 text(80,y,indent+title,col,11)
text(70,851,'PROJECT  •  LOCAL SOURCE', '#8b9ab9',10)

# center
rect((289,36,1102,92),'#171d31')
text(310,49,'◆  QEAPP STUDIO', '#b9afff',13)
for x,label,clr in [(604,'Open','#2d3450'),(690,'Save','#2d3450'),(765,'Validate','#2d3450'),(869,'Build','#2d3450'),(953,'▶ RUN F9','#6056be')]:
 ww=95 if x==953 else (92 if label=='Validate' else 75)
 rect((x,45,x+ww,80),clr,outline='#514c7e',r=6)
 text(x+10,55,label,'#e7e7ff',11)
rect((289,93,1102,132),'#191e32')
rect((303,98,449,131),'#303451')
rect((303,98,449,101),'#a794ff')
text(325,108,'◎  main.lua', '#f7f7ff',12)
text(475,109,'qeapp.project.json', '#8d9db8',11)
rect((289,132,1102,714),'#111728')
# gutters and code
rect((289,136,334,713),'#141a2b')
for i in range(19):
 yy=156+i*25
 text(305,yy,str(i+1), '#53617f',11,m=True)
lines=[
 ('-- Pixel Snake / Lua 5.4 host demo', '#7288ad'),
 ('local snake = { {8,8}, {7,8} }', '#e4c7a0'),
 ('local dir = {1,0}', '#e4c7a0'),
 ('local score = 0', '#dbc0e5'),
 ('', '#fff'),
 ('function on_init()', '#a6aaff'),
 ('    engine.clear(0x0000)', '#c0d9f3'),
 ('end', '#a6aaff'),
 ('', '#fff'),
 ('function on_key(key, down)', '#a6aaff'),
 ('    if not down then return end', '#d5c2ea'),
 ('    if key == "up" then', '#d5c2ea'),
 ('        dir = { 0,-1 }', '#b7e9c3'),
 ('    elseif key == "down" then', '#d5c2ea'),
 ('        dir = { 0, 1 }', '#b7e9c3'),
 ('    end', '#a6aaff'),
 ('end', '#a6aaff'),
 ('', '#fff'),
]
for i,(v,c) in enumerate(lines):
 text(353,156+i*25,v,c,13,m=True)
text(352,651,'-- F9 = live virtual phone   F8 = deterministic replay', '#768aa8',11,m=True)

rect((289,714,1102,892),'#141a2d')
text(311,729,'TERMINAL     OUTPUT     BUILD LOG', '#b8bfdd',11)
rect((312,764,1075,765),'#313c55')
for i,(line,col) in enumerate([
 ('[HOST] Lua 5.4 runtime built (C++17)', '#98deb6'),
 ('[VM] Lua source: projects/lua-snake/main.lua', '#b3bdd8'),
 ('[DEVICE] Interactive QEFRAME/1 • 240x270 RGB565', '#aaa2ed'),
 ('[VM] frame=14  heap_used=28409 B', '#8edab4'),
]):text(313,781+i*22,line,col,11,m=True)

# Virtual phone pane
rect((1103,36,1509,892),'#171b2d',outline='#353d58')
rect((1103,36,1509,93),'#1c2037')
text(1125,51,'▣  VIRTUAL DEVICE', '#dfdef8',12)
text(1380,52,'HOST  15 FPS', '#8ee4b1',10)
text(1141,103,'240 × 320   •   LUA HOST  •   LIVE', '#a4adca',11)
rect((1160,130,1444,700),'#242a43',outline='#556388',r=22,width=2)
text(1225,145,'V Q E A F    O S', '#b5c1fa',11)
rect((1177,175,1427,506),'#080b0f',outline='#648085',r=4,width=2)
image=Image.open(FRAME).convert('RGB').resize((240,320),Image.Resampling.NEAREST)
im.paste(image,(1182,181))
# Dpad controls rows
for row,keys in enumerate([('MENU','▲','BACK'),('◀','START','▶'),('OPTION','▼','B')]):
 for col,k in enumerate(keys):
  x=1178+col*83;y=521+row*39
  rect((x,y,x+76,y+33),'#3b4566' if k in ('START','▲','▼','◀','▶') else '#313850',outline='#59678b',r=6)
  text(x+(11 if len(k)>3 else 28),y+10,k,'#f1f4ff',10)
rect((1178,643,1420,675),'#343b58',outline='#59678b',r=5)
text(1209,651,'SELECT  •  GAME / T9', '#dbe0fa',10)
for x,label,fill in [(1129,'▶ RUN','#6454c0'),(1261,'■ STOP','#2d3854'),(1375,'▣ PNG','#2d3854')]:
 rect((x,723,x+102,763),fill,outline='#544d87',r=6)
 text(x+15,736,label,'#e4e4ff',11)
text(1148,782,'RUNNING  •  desktop VM', '#9dddad',12)
text(1114,856,'LOCAL LUA RUNTIME • NOT HARDWARE EMULATION', '#7c88ab',10)

rect((0,892,1510,919),'#35316d')
text(18,899,'●  QEAPP/2  |  main.lua  |  UTF-8  |  240×320  |  Build: host', '#e4e1fa',10)
text(1150,899,'UI CONCEPT MOCKUP • NOT Qt CAPTURE', '#ded3ff',10)
OUTPUT.parent.mkdir(exist_ok=True,parents=True)
im.save(OUTPUT,optimize=True)
print(OUTPUT)
