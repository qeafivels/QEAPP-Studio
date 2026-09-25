"""v0.4.1: hostile input drawing guards, Lua replay and source mirror gates."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/'build/qe_lua_host'
if os.name=='nt':RUNNER=RUNNER.with_suffix('.exe')

@unittest.skipUnless(RUNNER.is_file(),'Build tested host runner before testing Lua VM')
class InputAndBudget(unittest.TestCase):
    def runner(self,script,events=None,frames=3):
        with tempfile.TemporaryDirectory() as d:
            work=Path(d)
            source=work/'main.lua';source.write_text(script,encoding='utf8')
            ppm=work/'screen.ppm'
            argv=[str(RUNNER),str(source),str(ppm),str(frames),'192']
            if events is not None:
                f=work/'events.txt';f.write_text(events,encoding='ascii');argv.append(str(f))
            p=subprocess.run(argv,capture_output=True,text=True,timeout=6)
            return p,ppm.read_bytes() if ppm.exists() else b''
    def test_rect_clips_giant_coordinates_without_ub(self):
        app="""function on_draw()
            engine.rect(9223372036854775807,4,12,12,0xf800)
            engine.rect(-9223372036854775807,4,12,12,0xf800)
            engine.rect(-9,-9,14,14,0xf800)
        end"""
        p,image=self.runner(app,frames=1)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('rect=1',p.stdout)
        self.assertEqual(image[:15],b'P6\n240 270\n255\n')
        self.assertEqual(image[15:18],bytes([255,0,0]))
    def test_draw_calls_hard_limited(self):
        p,_=self.runner('function on_draw() for i=1,800 do engine.rect(1,1,2,2,0x07e0) end end',frames=1)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('draw call budget exceeded',p.stderr)
    def test_rgb565_overflow_rejected(self):
        p,_=self.runner('function on_draw() engine.clear(65536) end',frames=1)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('RGB565 color',p.stderr)
    def test_huge_text_does_not_draw(self):
        p,_=self.runner('function on_draw() engine.text(2,2,string.rep("x",49),65535) end',frames=1)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('text=0',p.stdout)
    def test_only_gameplay_keys_in_replay(self):
        p,_=self.runner('function on_key(k,v) end',events='0 menu 1\n')
        self.assertEqual(p.returncode,2)
        self.assertIn('reserved key',p.stderr)
    def test_deterministic_gameplay_key_sequence(self):
        app='''local x=0
function on_key(key,down) if down and key=="right" then x=x+1 end end
function on_draw() engine.rect(0,0,x,2,0xf800) end'''
        replay='0 right 1\n1 right 1\n2 right 1\n'
        p,image=self.runner(app,replay)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('input_events=3',p.stdout)
        self.assertEqual(image[15:15+3*3],bytes([255,0,0])*3)
    def test_project_json_replay_and_validation(self):
        sys.path.insert(0,str(ROOT/'tools'))
        from lua_preview import prepare_replay
        with tempfile.TemporaryDirectory() as d:
            work=Path(d)
            payload=work/'events.json';out=work/'events.txt'
            payload.write_text(json.dumps([{'frame':0,'key':'up','down':True},
                                           {'frame':1,'key':'up','down':False}]))
            self.assertEqual(prepare_replay(payload,out,3),2)
            self.assertIn('up 0',out.read_text())
            payload.write_text(json.dumps([{'frame':0,'key':'menu','down':True}]))
            with self.assertRaises(ValueError):prepare_replay(payload,out,3)

class DirectVmKeyGuard(unittest.TestCase):
    def test_runtime_rejects_os_reserved_keys_without_replay_parser(self):
        if not sys.platform.startswith('linux'):
            self.skipTest('Cross-platform official Lua source build validated separately')
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'keyguard'
            common=[str(ROOT/'runtime/src/QeLuaRuntime.cpp'),
                    str(ROOT/'runtime/host/tests/test_keyguard.cpp')]
            cmd=['g++','-std=c++17','-Wall','-Wextra','-O2',
                 '-I'+str(ROOT/'runtime/include'),
                 '-I'+str(ROOT/'runtime/host/compat'),*common,
                 '-Wl,-l:liblua5.4.so.0','-o',str(exe)]
            try:
                subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=35)
            except (OSError,subprocess.CalledProcessError) as exc:
                self.skipTest('System liblua5.4 diagnostic fallback unavailable: '+str(exc)[:150])
            p=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn('PASS',p.stdout)

class FirmwareContract(unittest.TestCase):
    def test_host_firmware_same_runtime_source(self):
        src=(ROOT/'runtime/src/QeLuaRuntime.cpp').read_text()
        target=(ROOT/'firmware/VQEAF-OS/src/lua/QeLuaRuntime.cpp').read_text()
        self.assertEqual(target, '#if defined(VQEAF_ENABLE_LUA) && VQEAF_ENABLE_LUA\n'+src+'\n#endif // VQEAF_ENABLE_LUA\n')
        header=(ROOT/'runtime/include/QeLuaRuntime.h').read_bytes()
        self.assertEqual(header,(ROOT/'firmware/VQEAF-OS/src/lua/QeLuaRuntime.h').read_bytes())
    def test_firmware_profile_optin_only(self):
        ini=(ROOT/'firmware/VQEAF-OS/platformio.ini').read_text()
        standard=ini.split('[env:vqeaf_os]',1)[1].split('[env:',1)[0]
        beta=ini.split('[env:vqeaf_lua_beta]',1)[1]
        self.assertNotIn('VQEAF_ENABLE_LUA=1',standard)
        self.assertIn('VQEAF_ENABLE_LUA=1',beta)
        self.assertIn('QE_LUA_PSRAM_ALLOC=1',beta)

if __name__=='__main__': unittest.main()
