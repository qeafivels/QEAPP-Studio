"""Parser safety and persistent real-host-Lua VM smoke (requires C++ binary)."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
from studio.core.frame_protocol import (
    FrameDecoder, FrameProtocolError, PIXEL_BYTES,WIDTH,HEIGHT,rgb565_to_rgb888
)
from studio.core.commands import build_lua_host

class StreamProtocolTests(unittest.TestCase):
    def test_partial_binary_frame(self):
        parser=FrameDecoder()
        wire=b'QEFRAME 0\n'+b'\x00\xf8'*(WIDTH*HEIGHT)
        self.assertEqual(parser.feed(wire[:2]),[])
        self.assertEqual(parser.feed(wire[2:4096]),[])
        frames=parser.feed(wire[4096:])
        self.assertEqual(len(frames),1)
        self.assertEqual(frames[0].sequence,0)
        self.assertEqual(len(frames[0].rgb565_le),PIXEL_BYTES)
        self.assertEqual(rgb565_to_rgb888(frames[0].rgb565_le)[:3],b'\xff\x00\x00')
        self.assertEqual(parser.feed(b'QEFRAME 1\n'+b'\x00\x00'*WIDTH*HEIGHT)[0].sequence,1)

    def test_protocol_refuses_corruption(self):
        for raw in (b'BAD\n',b'QEFRAME nope\n',b'QEFRAME -1\n', b'X'*41):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(FrameProtocolError):FrameDecoder().feed(raw)
        p=FrameDecoder()
        p.feed(b'QEFRAME 0\n'+b'\xff'*PIXEL_BYTES)
        with self.assertRaises(FrameProtocolError):p.feed(b'QEFRAME 2\n')
        with self.assertRaises(FrameProtocolError):rgb565_to_rgb888(b'broken')

    def test_job_does_not_unexpectedly_use_system_lua(self):
        old=os.environ.pop('QEAPP_HOST_SYSTEM_LUA',None)
        try:
            self.assertNotIn('--system-lua',build_lua_host().argv)
            os.environ['QEAPP_HOST_SYSTEM_LUA']='1'
            self.assertIn('--system-lua',build_lua_host().argv)
        finally:
            if old is None:os.environ.pop('QEAPP_HOST_SYSTEM_LUA',None)
            else:os.environ['QEAPP_HOST_SYSTEM_LUA']=old

class InteractiveHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe=ROOT/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')
        cls.exe=exe if exe.is_file() else None

    def test_real_lua_host_keyboard_frames(self):
        if self.exe is None:self.skipTest('Lua host binary not built (build_lua_host.py)')
        from tools.virtual_phone_cli import capture
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'frame.png'
            res=capture(ROOT/'projects/lua-snake/main.lua',path,8,'start',self.exe)
            self.assertEqual(res['frames'],8)
            self.assertTrue(path.read_bytes().startswith(b'\x89PNG'))
            self.assertGreater(path.stat().st_size,150)
            self.assertFalse(res['hardware_tested'])

    def test_30_frames_report_bounded_host_metrics(self):
        if self.exe is None:self.skipTest('Lua host binary not built')
        from tools.virtual_phone_cli import capture
        with tempfile.TemporaryDirectory() as d:
            result = capture(ROOT/'projects/lua-snake/main.lua', Path(d)/'frame.png', 30, exe=self.exe)
            self.assertEqual(result['frames'],30)
            self.assertFalse(result['hardware_tested'])
            self.assertIsNotNone(result['host_metric'])
            self.assertEqual(result['host_metric']['frame'],30)
            self.assertGreater(result['host_metric']['render_us'],0)
            self.assertGreater(result['host_metric']['peak_bytes'],0)
            self.assertGreater(result['host_throughput_fps'],0)

    def test_reserved_keys_rejected_by_real_host(self):
        if self.exe is None:self.skipTest('Lua host binary not built')
        proc=subprocess.run([str(self.exe),str(ROOT/'projects/lua-hello/main.lua'),'--interactive'],
             input=b'KEY menu 1\n',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=6)
        self.assertEqual(proc.returncode,2)
        self.assertIn(b'Unsupported emulator key',proc.stderr)

    def test_bad_script_rejected(self):
        if self.exe is None:self.skipTest('Lua host binary not built')
        proc=subprocess.run([str(self.exe),'/nonexistent/new.lua','--interactive'],
             input=b'',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=6)
        self.assertNotEqual(proc.returncode,0)
        self.assertIn(b'Script missing',proc.stderr)

if __name__=='__main__':unittest.main()
