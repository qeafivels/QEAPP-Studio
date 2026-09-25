"""M1 verification: compile/execute same portable C++ core, compare screenshots."""
import importlib.util
import pathlib
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('simulate_host',ROOT/'tools/simulate_host.py')
sim=importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

@unittest.skipUnless(shutil.which('g++') or shutil.which('clang++'),'C++17 compiler not installed')
class HostEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=pathlib.Path(cls.temp.name)
        cc=shutil.which('g++') or shutil.which('clang++')
        cmd=[cc,'-std=c++17','-O2','-Wall','-Wextra','-Werror','-pedantic',
            '-I',str(ROOT/'engine/include'),'-I',str(ROOT/'engine/host'),
            str(ROOT/'engine/src/runtime.cpp'),str(ROOT/'engine/src/draw.cpp'),
            str(ROOT/'engine/host/HostCanvas.cpp'),str(ROOT/'tests/test_engine.cpp'),
            '-o',str(cls.root/'test_engine')]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=80)
        if p.returncode: raise AssertionError(p.stderr)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_native_engine(self):
        result=subprocess.run([str(self.root/'test_engine')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('PASS test_engine',result.stdout)
    def test_host_screenshots_deterministic_and_png_crc(self):
        digests={}
        for scene in ('ready','playing','paused'):
            p1=self.root/(scene+'_1.png');p2=self.root/(scene+'_2.png')
            r1=sim.simulate(p1,scene,40);r2=sim.simulate(p2,scene,40)
            self.assertEqual(r1['png_sha256'],r2['png_sha256'])
            self.assertEqual(r1['rgb_sha256'],r2['rgb_sha256'])
            self.assertEqual(r1['width'],240);self.assertEqual(r1['height'],320)
            self.assertEqual(r1['status'],'HOST_ONLY_PASS')
            data=p1.read_bytes();self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II',data[16:24]),(240,320))
            digests[scene]=r1['rgb_sha256']
        self.assertEqual(len(set(digests.values())),3)
    def test_hello_app_uses_same_engine(self):
        ready=sim.simulate(self.root/'hello_ready.png','ready',40,demo='hello')
        playing=sim.simulate(self.root/'hello_playing.png','playing',40,demo='hello')
        self.assertNotEqual(ready['rgb_sha256'],playing['rgb_sha256'])
        self.assertEqual(playing['demo'],'hello')
        self.assertEqual(playing['width'],240)
    def test_golden_rgb565_lossless_render(self):
        import json
        golden=json.loads((ROOT/'tests/golden/host_sha256.json').read_text())
        for key, expected in golden.items():
            demo, scene, frames=key.split(':')
            result=sim.simulate(self.root/(key.replace(':','_')+'.png'),scene,int(frames),demo=demo)
            self.assertEqual(result['rgb_sha256'],expected['rgb_sha256'])
            self.assertEqual(result['png_sha256'],expected['png_sha256'])
    def test_long_run_and_bounds(self):
        r=sim.simulate(self.root/'long.png','playing',1200)
        self.assertEqual(r['status'],'HOST_ONLY_PASS')
        self.assertIn('input_overflows=0',r['runtime_log'])
        with self.assertRaises(sim.SimulatorError):
            sim.simulate(self.root/'bad.png','playing',2001)
    def test_lua_requires_explicit_firmware_profile(self):
        text=(ROOT/'tools/qstudio.py').read_text()
        self.assertIn("('web','text','lua')",text)
        self.assertIn("--experimental-lua",text)
        self.assertIn("vqeaf_lua_beta",text)
if __name__=='__main__':unittest.main()
