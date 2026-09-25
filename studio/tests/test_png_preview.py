"""Host-only asset preview safety: do not decode untrusted PNG on ESP32."""
from __future__ import annotations
import pathlib
import struct
import tempfile
import unittest
import zlib
from studio.core.workspace import Workspace, WorkspaceError

def png(w=3, h=2) -> bytes:
    def chunk(tag: bytes, body: bytes) -> bytes:
        return struct.pack('>I',len(body))+tag+body+struct.pack('>I',zlib.crc32(tag+body)&0xffffffff)
    # 8-bit RGB rows (filter 0)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\0'*(3*w))*h))+chunk(b'IEND',b'')

class BinaryWorkspacePreview(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        (self.root/'qeapp.project.json').write_text('{"type":"lua"}',encoding='utf8')
        (self.root/'assets').mkdir()
        (self.root/'assets/small.png').write_bytes(png())
        self.ws=Workspace(self.root)
    def test_small_png_list_and_preview_without_edit_access(self):
        self.assertIn('assets/small.png',self.ws.iter_files())
        self.assertEqual(self.ws.read_png_preview('assets/small.png'),png())
        with self.assertRaises(WorkspaceError):self.ws.read('assets/small.png')
    def test_large_header_and_wrong_magic(self):
        (self.root/'assets/large.png').write_bytes(png(10000,2))
        with self.assertRaises(WorkspaceError):self.ws.read_png_preview('assets/large.png')
        self.assertNotIn('assets/large.png',self.ws.iter_files())
        (self.root/'assets/spoof.png').write_bytes(b'just text')
        with self.assertRaises(WorkspaceError):self.ws.read_png_preview('assets/spoof.png')
    def test_reject_escape_and_symlink(self):
        for invalid in ('../x.png','/tmp/x.png','.git/config.png','build/y.png','assets\\small.png'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(WorkspaceError):self.ws.read_png_preview(invalid)
        symlink=self.root/'assets/aliased.png'
        try:symlink.symlink_to(self.root/'assets/small.png')
        except (OSError,NotImplementedError):self.skipTest('Symlinks unsupported by target OS')
        with self.assertRaises(WorkspaceError):self.ws.read_png_preview('assets/aliased.png')
    def test_refuse_oversize_input(self):
        (self.root/'assets/too-big.png').write_bytes(png()+(b'X'*1024*1024))
        with self.assertRaises(WorkspaceError):self.ws.read_png_preview('assets/too-big.png')

if __name__=='__main__':unittest.main()
