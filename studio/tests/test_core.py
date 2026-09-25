"""No Qt required: repeatable tests for the IDE's actual project/job core."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from studio.core import commands
from studio.core.config import StudioConfig
from studio.core.jobs import JobBusy, JobRunner
from studio.core.workspace import Workspace, WorkspaceError, MAX_EDITOR_BYTES

ROOT = Path(__file__).resolve().parents[2]

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project/'qeapp.project.json').write_text('{}', encoding='utf-8')
        self.ws = Workspace(self.project)

    def test_read_save_atomic_and_change_detection(self):
        doc = self.ws.read('qeapp.project.json')
        edited = self.ws.save('qeapp.project.json', '{"ok":true}\n', doc.sha256)
        self.assertEqual(self.ws.read('qeapp.project.json').sha256, edited.sha256)
        (self.project/'qeapp.project.json').write_text('{"external":true}')
        with self.assertRaisesRegex(WorkspaceError,'changed'):
            self.ws.save('qeapp.project.json', 'lost', edited.sha256)
        self.assertEqual((self.project/'qeapp.project.json').read_text(),'{"external":true}')

    def test_create_reject_overwrite(self):
        self.ws.save('main.lua', 'return true\n', None)
        with self.assertRaises(WorkspaceError):
            self.ws.save('main.lua', 'overwrite', None)

    def test_reject_unsafe_paths(self):
        for rel in ('../secret.txt', 'src/../../foo.lua', '/tmp/lua.lua',
                    'dist/private.lua', '.git/config.json', 'sub\\foo.lua',
                    'private.pem', 'payload.qeapp', '.hidden/main.lua'):
            with self.subTest(rel=rel), self.assertRaises(WorkspaceError):
                self.ws.path(rel, create=True)

    def test_create_safe_folders(self):
        self.ws.mkdir('assets')
        self.ws.mkdir('assets/sprites')
        self.ws.save('assets/sprites/map.lua', 'return {}', None)
        self.assertIn('assets/sprites/map.lua', self.ws.iter_files())
        for unsafe in ('../pwn', '.git/hooks', 'dist', '/tmp/out'):
            with self.assertRaises(WorkspaceError):
                self.ws.mkdir(unsafe)

    def test_reject_symlink_even_inside_project(self):
        (self.project/'real.lua').write_text('print("safe")')
        link = self.project/'alias.lua'
        try: link.symlink_to(self.project/'real.lua')
        except (OSError, NotImplementedError): self.skipTest('No symlink privileges')
        with self.assertRaisesRegex(WorkspaceError, 'Symlink'):
            self.ws.read('alias.lua')
        self.assertNotIn('alias.lua', self.ws.iter_files())

    def test_reject_oversize_binary_invalid_utf8(self):
        (self.project/'bad.lua').write_bytes(b'\xff')
        with self.assertRaisesRegex(WorkspaceError, 'UTF-8'):
            self.ws.read('bad.lua')
        (self.project/'bad.lua').write_bytes(b'\x00')
        with self.assertRaisesRegex(WorkspaceError, 'Binary'):
            self.ws.read('bad.lua')
        with self.assertRaisesRegex(WorkspaceError, '1 MiB'):
            self.ws.save('big.lua', 'x'*(MAX_EDITOR_BYTES+1), None)

    def test_explorer_does_not_show_key_or_build_folder(self):
        (self.project/'main.lua').write_text('ok')
        (self.project/'private.pem').write_text('DO_NOT_EXPOSE')
        (self.project/'dist').mkdir()
        (self.project/'dist'/'test.txt').write_text('hidden')
        files = self.ws.iter_files()
        self.assertIn('main.lua', files)
        self.assertNotIn('private.pem', files)
        self.assertNotIn('dist/test.txt', files)

class ConfigurationTests(unittest.TestCase):
    def test_preferences_never_accept_credentials(self):
        with tempfile.TemporaryDirectory() as d:
            conf = StudioConfig(Path(d)/'prefs.json')
            conf.update(firmware_root='C:/src/firmware',recent_projects=['A', 'A', 'B'])
            self.assertEqual(conf.data['recent_projects'], ['A','B'])
            self.assertNotIn('key',json.dumps(conf.data))
            with self.assertRaises(ValueError):
                conf.update(signing_key='C:/private.pem')
            self.assertNotIn('private.pem',conf.file.read_text())
            self.assertEqual(StudioConfig(conf.file).data['firmware_root'], 'C:/src/firmware')

class CommandTests(unittest.TestCase):
    def test_native_preview_is_only_host(self):
        spec = commands.simulate('snake','ready',Path('/tmp/sample.png'))
        self.assertIn('simulate',spec.argv)
        self.assertIn('host',spec.label.lower())
        with self.assertRaises(ValueError): commands.simulate('foreign','playing',Path('/tmp/foo'))
    def test_builder_never_keeps_key_in_labels(self):
        key = Path('/private/signing.pem')
        spec = commands.build(Path('/tmp/project'),Path('/tmp/fw'),key,
                              Path('/tmp/out.qeapp'),0x31534351)
        self.assertEqual(spec.secrets,(str(key),))
        self.assertNotIn(str(key),spec.label)
        self.assertEqual(spec.argv[1],str(commands.CLI))

class ProcessTests(unittest.TestCase):
    def test_streaming_redaction(self):
        runner = JobRunner()
        lines = []
        marker = 'TEST_PRIVATE_PATH_987'
        spec = commands.JobSpec(
            [sys.executable,'-c',f'print({marker!r})'], 'test',
            secrets=(marker,), timeout=10)
        self.assertEqual(runner.execute(spec,lines.append),0)
        self.assertIn('[REDACTED]', ''.join(lines))
        self.assertNotIn(marker, ''.join(lines))
        self.assertFalse(runner.running)

    def test_timeout(self):
        runner=JobRunner()
        lines=[]
        spec=commands.JobSpec([sys.executable,'-c','import time; time.sleep(8)'], 'timeout', timeout=.2)
        begin=time.monotonic()
        self.assertEqual(runner.execute(spec,lines.append),124)
        self.assertLess(time.monotonic()-begin,5)
        self.assertFalse(runner.running)
        self.assertIn('TIMEOUT',''.join(lines))

    def test_cancel(self):
        runner = JobRunner()
        result=[]
        started=threading.Event()
        spec=commands.JobSpec([sys.executable,'-u','-c',
                 'import time; print("RUNNING",flush=True); time.sleep(20)'], 'test', timeout=30)
        t=threading.Thread(target=lambda:result.append(runner.execute(spec,
                           lambda txt:started.set() if 'RUNNING' in txt else None)))
        t.start()
        self.assertTrue(started.wait(5))
        self.assertTrue(runner.cancel())
        t.join(timeout=8)
        self.assertFalse(t.is_alive())
        self.assertNotEqual(result[0],0)
        self.assertFalse(runner.running)

    def test_no_second_concurrent_build(self):
        runner=JobRunner()
        started=threading.Event()
        t=threading.Thread(target=lambda:runner.execute(commands.JobSpec(
             [sys.executable,'-u','-c','import time;print("READY",flush=True);time.sleep(20)'],
             'sleep',timeout=30),lambda x: started.set()))
        t.start()
        self.assertTrue(started.wait(5))
        with self.assertRaises(JobBusy):
            runner.execute(commands.JobSpec([sys.executable,'-c','print(1)'],'other'), lambda _:None)
        self.assertTrue(runner.cancel())
        t.join(8)
        self.assertFalse(t.is_alive())

class GuiSourceContract(unittest.TestCase):
    def test_gui_compiles_without_importing_qt(self):
        import ast
        for f in (ROOT/'studio'/'main.py',ROOT/'studio'/'gui'/'window.py'):
            ast.parse(f.read_text(encoding='utf-8'),filename=str(f))

if __name__ == '__main__':unittest.main()
