"""QEAPP Studio v0.4: VM/resource caps, signed Lua package, beta compatibility."""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FW=ROOT/'firmware/VQEAF-OS'
RUNNER=ROOT/'build/qe_lua_host'
spec=importlib.util.spec_from_file_location('qe_tool',ROOT/'tools/qstudio.py')
qe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(qe)

@unittest.skipUnless(RUNNER.is_file(),'Run python tools/bootstrap_lua.py and tools/build_lua_host.py for Lua VM tests')
class LuaVmTests(unittest.TestCase):
    def run_source(self,source: str,frames: int=1,memory: int=192):
        with tempfile.TemporaryDirectory() as work:
            lua=Path(work)/'s.lua';lua.write_text(source,encoding='utf8')
            return subprocess.run([str(RUNNER),str(lua),str(Path(work)/'preview.ppm'),str(frames),str(memory)],
                                  capture_output=True,text=True,timeout=7)
    def test_renders_hello_project(self):
        out=subprocess.run([str(RUNNER),str(ROOT/'projects/lua-hello/main.lua')],
                           capture_output=True,text=True,timeout=7)
        self.assertEqual(out.returncode,0,out.stderr)
        self.assertIn('PASS Lua 5.4',out.stdout)
    def test_restricted_globals_and_engine_only(self):
        out=self.run_source('''assert(io == nil and os == nil and package == nil)
assert(debug == nil and dofile == nil and loadfile == nil and load == nil)
assert(collectgarbage == nil and string.dump == nil)
assert(engine.rect and engine.text and engine.clear and engine.width==240)
function on_draw() engine.clear(0) end''')
        self.assertEqual(out.returncode,0,out.stderr)
    def test_infinite_top_level_stopped(self):
        out=self.run_source('while true do end')
        self.assertNotEqual(out.returncode,0)
        self.assertIn('budget exceeded',out.stderr)
    def test_infinite_frame_callback_stopped(self):
        out=self.run_source('function on_update(dt) while true do end end')
        self.assertNotEqual(out.returncode,0)
        self.assertIn('budget exceeded',out.stderr)
    def test_large_allocation_stopped(self):
        out=self.run_source("local x=string.rep('X',600000)")
        self.assertNotEqual(out.returncode,0)
    def test_lua_bytecode_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            path=Path(work)/'code.lua';path.write_bytes(b'\x1bLua\0\0hello')
            out=subprocess.run([str(RUNNER),str(path)],capture_output=True,text=True,timeout=7)
            self.assertNotEqual(out.returncode,0)
    def test_invalid_memory_budget(self):
        out=self.run_source('return true',memory=1025)
        self.assertNotEqual(out.returncode,0)
    def test_lua_host_png_dimensions(self):
        with tempfile.TemporaryDirectory() as work:
            out=Path(work)/'screen.png'
            env=os.environ.copy();env['QEAPP_HOST_SYSTEM_LUA']='1'
            pr=subprocess.run([sys.executable,str(ROOT/'tools/qstudio.py'),'lua-preview',
                 str(ROOT/'projects/lua-hello'),'--frames','3','-o',str(out)],
                 capture_output=True,text=True,timeout=20,env=env)
            self.assertEqual(pr.returncode,0,pr.stderr)
            self.assertEqual(out.read_bytes()[:8],b'\x89PNG\r\n\x1a\n')

class SignerTests(unittest.TestCase):
    def test_lua_optin_signature_and_tamper(self):
        try:
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            self.skipTest('cryptography not installed')
        with tempfile.TemporaryDirectory() as work:
            d=Path(work)
            key=ec.generate_private_key(ec.SECP256R1())
            priv=d/'private.pem';pub=d/'public.pem'
            priv.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            pub.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
            dst=d/'app.qeapp';args=[sys.executable,str(ROOT/'tools/qstudio.py'),'build',str(ROOT/'projects/lua-hello'),
                '--firmware-root',str(FW),'--sign-key',str(priv),'-o',str(dst)]
            blocked=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(blocked.returncode,2,blocked.stderr)
            self.assertNotIn(str(priv),blocked.stderr)
            good=subprocess.run(args+['--experimental-lua'],capture_output=True,text=True)
            self.assertEqual(good.returncode,0,good.stderr)
            m=qe.inspect(dst,pub,0x544c5541)
            self.assertEqual((m['type'],m['signature']),('lua','PASS (against supplied PEM only)'))
            raw=bytearray(dst.read_bytes());raw[-1]^=1;dst.write_bytes(raw)
            with self.assertRaises(qe.ProjectError):qe.inspect(dst,pub,0x544c5541)
            priv.unlink();pub.unlink()
    def test_lua_manifest_and_project_validation(self):
        obj,files=qe.validate(ROOT/'projects/lua-hello')
        self.assertEqual((obj['type'],files['content'].suffix),('lua','.lua'))

if __name__=='__main__':unittest.main()
