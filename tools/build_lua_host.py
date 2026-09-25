#!/usr/bin/env python3
"""Build desktop host runner from the SAME bounded VM as ESP32 firmware.
Default: official Lua vendor source installed by bootstrap_lua.py.
--system-lua is a Linux-only diagnostic fallback for environments with the
liblua5.4 shared library but no network; never used for firmware/release builds.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys
from studio_firmware import firmware_root
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--system-lua',action='store_true');p.add_argument('--output',type=Path,default=ROOT/'build'/('qe_lua_host.exe' if sys.platform=='win32' else 'qe_lua_host'))
 a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
 base=ROOT/'runtime';files=[base/'src/QeLuaRuntime.cpp',base/'host/qe_lua_host.cpp']
 opts=['g++','-std=c++17','-O2','-Wall','-Wextra','-I'+str(base/'include')]
 if a.system_lua:
  opts += ['-I'+str(base/'host/compat')]
  libs=['-Wl,-l:liblua5.4.so.0']
 else:
  fw=firmware_root(required=True)
  vendor=fw/'lib/VqeafLua54/src'
  if not (vendor/'lua.h').exists():
   sys.exit('Run python tools/bootstrap_lua.py first (official Lua 5.4.8)')
  opts+=['-I'+str(vendor)]
  cfiles=[str(f) for f in vendor.glob('*.c')]
  cfiles=[f for f in cfiles if Path(f).name not in ('lua.c','luac.c','onelua.c')]
  objs=[]
  for path in cfiles:
   obj=a.output.parent/(Path(path).name+'.o')
   subprocess.run(['gcc','-std=c99','-O2','-I'+str(vendor),'-c',path,'-o',str(obj)],check=True)
   objs.append(str(obj))
  libs=objs+['-lm']+(['-ldl'] if sys.platform.startswith('linux') else [])
 cmd=opts+[str(x) for x in files]+libs+['-o',str(a.output)]
 subprocess.run(cmd,check=True)
 print('Host runner:',a.output)
if __name__=='__main__':main()
