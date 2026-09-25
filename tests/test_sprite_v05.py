"""Pixel art end-to-end: PNG converter -> signed Lua project -> shared VM -> RGB565."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.pixel_sprite import lua_snippet, pack_mask, SpriteError
from tools.qstudio import init_project, validate
RUNNER=ROOT/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')

class PackMask(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:from PIL import Image
        except ImportError:raise unittest.SkipTest('Pillow not installed; no PNG conversion test evidence')
        cls.Image=Image

    def test_odd_width_packed_msb_first_and_zero_padding(self):
        im=self.Image.new('RGBA',(3,3),(0,0,0,0))
        for x,y in ((0,0),(2,0),(1,1),(0,2),(2,2)):
            im.putpixel((x,y),(240,220,200,255))
        self.assertEqual(pack_mask(im),(3,3,b'\xaa\x80'))

    def test_mode_alpha_dark_light_and_exact_alpha(self):
        im=self.Image.new('RGBA',(3,1))
        im.putdata([(255,255,255,0),(0,0,0,127),(255,255,255,255)])
        self.assertEqual(pack_mask(im,'alpha',128)[2],b'\x20')
        self.assertEqual(pack_mask(im,'dark',120)[2],b'\x40')
        self.assertEqual(pack_mask(im,'light',128)[2],b'\x20')

    def test_reject_wrong_geometry_name_and_symlink(self):
        with self.assertRaises(SpriteError):pack_mask(self.Image.new('RGBA',(33,1)))
        with self.assertRaises(SpriteError):pack_mask(self.Image.new('RGBA',(1,1)),'x')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.png';self.Image.new('RGBA',(2,2)).save(p)
            with self.assertRaises(SpriteError):lua_snippet(p,'invalid-code();')
            if os.name != 'nt':
                link=Path(d)/'link.png';link.symlink_to(p)
                with self.assertRaises(SpriteError):lua_snippet(link)

    def test_inlined_sprite_is_only_runtime_dependency(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'u.png';self.Image.new('RGBA',(1,1),(255,0,0,255)).save(p)
            s=lua_snippet(p,'tiny')
            self.assertIn('local tiny_bits = "\\x80"',s)
            self.assertNotIn(str(p),s)

@unittest.skipUnless(RUNNER.is_file(),'Build shared host VM before exercising C++ blit1')
class RuntimeBlit(unittest.TestCase):
    def run_lua(self,script: str):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'main.lua';ppm=Path(d)/'frame.ppm'
            path.write_text(script,encoding='utf-8')
            p=subprocess.run([str(RUNNER),str(path),str(ppm),'1','192'],capture_output=True,text=True,timeout=8)
            return p,ppm.read_bytes() if ppm.exists() else b''

    def test_lossless_msb_and_transparent_runs(self):
        script='''function on_draw()
 engine.clear(0x0000)
 engine.blit1(0,0,3,3,"\\xAA\\x80",0xF800)
end'''
        p,data=self.run_lua(script)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('rect=6',p.stdout) # clear + five opaque runs
        payload=data.split(b'\n',3)[3]
        get=lambda x,y:payload[(y*240+x)*3:(y*240+x+1)*3]
        for y in range(3):
            for x in range(3):
                red=(x,y) in {(0,0),(2,0),(1,1),(0,2),(2,2)}
                self.assertEqual(get(x,y),b'\xff\0\0' if red else b'\0\0\0')

    def test_right_and_bottom_clipping(self):
        p,img=self.run_lua('function on_draw() engine.blit1(239,269,3,3,"\\xFF\\x80",0x07E0) end')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('rect=1',p.stdout)
        data=img.split(b'\n',3)[3]
        self.assertEqual(data[((269*240+239)*3):((269*240+239)*3+3)],bytes((0,255,0)))

    def test_reject_short_payload_noncanonical_tail_and_color(self):
        programs=[
          ('engine.blit1(1,1,3,3,"\\x80",65535)', 'exact packed payload'),
          ('engine.blit1(1,1,3,3,"\\x80\\x81",65535)', 'trailing padding bits'),
          ('engine.blit1(1,1,33,1,"\\xFF\\xFF\\xFF\\xFF\\x80",65535)', 'width/height'),
          ('engine.blit1(1,1,1,1,"\\x80",65536)', 'RGB565 color'),
        ]
        for call,err in programs:
            with self.subTest(err=err):
                p,_=self.run_lua('function on_draw() '+call+' end')
                self.assertNotEqual(p.returncode,0)
                self.assertIn(err,p.stderr)

    def test_exceeded_budget_preflight_does_not_partially_blit(self):
        # One 32x32 checkerboard is 512 one-pixel runs. Two would need 1024.
        bits=bytearray(128)
        for y in range(32):
            for x in range(32):
                if (x+y)%2==0:
                    bit=y*32+x;bits[bit//8]|=0x80>>(bit%8)
        esc=''.join(f'\\x{b:02X}' for b in bits)
        p,_=self.run_lua('function on_draw() engine.blit1(0,0,32,32,"'+esc+'",0xffff) engine.blit1(0,0,32,32,"'+esc+'",0xffff) end')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('budget exceeded (blit1)',p.stderr)

    def test_sample_game_is_valid_and_previews(self):
        project=ROOT/'projects/lua-sprite'
        obj,_=validate(project);self.assertEqual(obj['type'],'lua')
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'sprite.ppm'
            p=subprocess.run([str(RUNNER),str(project/'main.lua'),str(output),'8','192'],capture_output=True,text=True,timeout=8)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('PASS Lua 5.4',p.stdout)
            self.assertTrue(output.read_bytes().startswith(b'P6\n240 270\n255\n'))

class MirrorAndScaffold(unittest.TestCase):
    def test_firmware_is_identical_to_host_vm(self):
        native=(ROOT/'runtime/src/QeLuaRuntime.cpp').read_text()
        embedded=(ROOT/'firmware/VQEAF-OS/src/lua/QeLuaRuntime.cpp').read_text()
        self.assertEqual(embedded,'#if defined(VQEAF_ENABLE_LUA) && VQEAF_ENABLE_LUA\n'+native+'\n#endif // VQEAF_ENABLE_LUA\n')
        self.assertEqual((ROOT/'runtime/include/QeLuaRuntime.h').read_bytes(),
                         (ROOT/'firmware/VQEAF-OS/src/lua/QeLuaRuntime.h').read_bytes())
        self.assertIn('VQEAF_ENABLE_LUA=1',(ROOT/'firmware/VQEAF-OS/platformio.ini').read_text())

    def test_new_template_scaffold(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)/'ship'
            init_project('lua-sprite',t,'ship_game','Ship Game')
            obj,_=validate(t)
            self.assertEqual((obj['id'],obj['type']),('ship_game','lua'))
            self.assertTrue((t/'assets/ship_16x16.png').is_file())

if __name__=='__main__':unittest.main()
