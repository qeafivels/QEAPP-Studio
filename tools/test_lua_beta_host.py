#!/usr/bin/env python3
"""Host stubs: build/link complete beta firmware incl Lua runtime and parser.
A host success is NEVER equivalent to PlatformIO/ESP32-S3 verification.
"""
from pathlib import Path
from studio_firmware import firmware_root
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
FW=firmware_root(required=True)
STUB=FW/'tools/host_stubs'
COMPAT=ROOT/'runtime/host/compat'
FLAGS=['-std=c++11','-fpermissive','-DVQEAF_ENABLE_LUA=1','-DQE_LUA_PSRAM_ALLOC=1','-DARDUINO',
 '-DQEAPP_HOST_STUB_CRYPTO=1','-DTFT_DC=47','-DTFT_CS=14','-DTFT_RST=3',
 '-I'+str(STUB),'-I'+str(COMPAT),'-I'+str(FW/'include'),'-I'+str(FW/'src')]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError('Host beta build failed: '+' '.join(str(x) for x in cmd)+'\n'+p.stderr[-6000:])
 return p
if __name__=='__main__':
 with tempfile.TemporaryDirectory(prefix='vqeaf-lua-beta-link-') as work:
  tmp=Path(work);files=sorted((FW/'src').rglob('*.cpp'));objs=[]
  for i,path in enumerate(files):
   obj=tmp/(str(i)+'.o')
   run(['g++',*FLAGS,'-c',str(path),'-o',str(obj)])
   objs.append(str(obj))
  run(['g++',*FLAGS,*objs,str(STUB/'host_globals.cpp'),str(STUB/'host_entry.cpp'),
       '-Wl,-l:liblua5.4.so.0','-o',str(tmp/'linked')])
  print(f'PASS beta: {len(files)} C++ translation units + full mock host firmware link')
  for beta in (False,True):
   exe=tmp/('test_beta' if beta else 'test_stock')
   run(['g++','-std=c++11']+(['-DVQEAF_ENABLE_LUA=1'] if beta else [])+[
       '-I'+str(FW/'src/services'),str(ROOT/'runtime/host/tests/test_parser.cpp'),
       str(FW/'src/services/QeappFormat.cpp'),'-o',str(exe)])
   out=run([str(exe)]);print(out.stdout.strip())
 print('NOTE: ESP32-S3 target build and PSRAM allocation are NOT verified')
