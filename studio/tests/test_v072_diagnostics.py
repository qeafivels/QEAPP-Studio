"""v0.7.2 regression: real host VM, opt-in diagnostics and non-destructive repair."""
from __future__ import annotations
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
from studio.core.diagnostics import DebugSession, guest_error, write_error
from studio.core import repair
from tools import studio_launcher as launcher


class DiagnosticsTests(unittest.TestCase):
    def test_guest_line_parser_bounded_and_unknown_source(self):
        self.assertEqual(guest_error('Lua VM frame FAIL: signed-qeapp-main.lua:12: nil value'),(12,'nil value'))
        self.assertEqual(guest_error('Lua startup FAIL: signed-qeapp-main.lua:3: syntax'),(3,'syntax'))
        self.assertIsNone(guest_error('Lua startup FAIL: /tmp/secret.lua:10: no'))
        self.assertIsNone(guest_error('x'*2049))

    def test_debug_session_never_serializes_script_or_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            log=DebugSession(Path(d))
            log.record('key', key='up', down=True, token='SECRET', script='private project.lua')
            log.record('frame', fps=15, heap=1024, source='SECRET')
            log.record('invalid', password='SECRET')
            log.stop()
            log.record('frame',heap=100)
            raw=log.path.read_text()
            self.assertEqual(len(raw.splitlines()),2)
            self.assertNotIn('SECRET',raw)
            self.assertNotIn('project.lua',raw)
            self.assertEqual(json.loads(raw.splitlines()[0])['key'],'up')

    def test_error_log_rotates(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'gui-errors.log'
            target.write_bytes(b'x'*1_000_050)
            write_error('test','diagnostics',target)
            self.assertLess(target.stat().st_size,1024)
            self.assertTrue(target.with_suffix('.previous.log').exists())

    def test_repair_dry_run_and_explicit_settings_backup(self):
        with tempfile.TemporaryDirectory() as d:
            settings=Path(d)/'QEAPPStudio/settings.json'
            settings.parent.mkdir()
            settings.write_text('{BROKEN SECRET',encoding='utf-8')
            root=Path(d)
            before=settings.read_bytes()
            checks=repair.inspect(settings,root)
            self.assertTrue(next(x for x in checks if x.name=='User settings').repairable)
            self.assertEqual(settings.read_bytes(),before,'Inspect must not mutate')
            backup=repair.apply(settings)
            self.assertEqual(backup.read_bytes(),before)
            self.assertEqual(json.loads(settings.read_text())['recent_projects'],[])
            self.assertIsNone(repair.apply(settings),'valid data must not be reset')
            self.assertTrue(backup.is_file())

    def test_valid_settings_are_never_reset(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'settings.json'
            raw='{"recent_projects":["C:/my project"],"firmware_root":"foo"}'
            path.write_text(raw)
            self.assertFalse(any(x.repairable for x in repair.inspect(path,Path(d))))
            self.assertIsNone(repair.apply(path))
            self.assertEqual(path.read_text(),raw)

    def test_launcher_broken_venv_repair_creates_backup_without_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            venv=Path(d)/'.venv'
            interpreter=launcher.python_in_venv(venv)
            interpreter.parent.mkdir(parents=True)
            interpreter.write_text('broken interpreter marker')
            reporter=launcher.Reporter(Path(d)/'launcher.log')
            def fake_run(command, reporter, **kwargs):
                if '-m' in command and 'venv' in command:
                    interpreter.parent.mkdir(parents=True,exist_ok=True)
                    interpreter.write_text('recreated python marker')
                return 0
            with patch.object(launcher,'VENV',venv), \
                 patch.object(launcher,'is_venv_working',side_effect=[False,True]), \
                 patch.object(launcher,'run',side_effect=fake_run):
                value=launcher.ensure_python(launcher.Options(repair=True),reporter)
            self.assertEqual(value,launcher.python_in_venv(venv))
            copies=list(Path(d).glob('.venv.broken-*'))
            self.assertEqual(len(copies),1)
            self.assertTrue((copies[0]/interpreter.relative_to(venv)).exists())

    def test_window_source_has_real_connected_doctor_and_problem(self):
        tree=ast.parse((ROOT/'studio/gui/window.py').read_text(encoding='utf-8'))
        methods={n.name for cls in tree.body if isinstance(cls,ast.ClassDef) and cls.name=='StudioWindow'
                    for n in cls.body if isinstance(n,ast.FunctionDef)}
        for name in ('safe_repair_mode','run_gui_doctor','open_problem','on_guest_problem',
                     'reset_layout','restart_virtual_machine'):
            self.assertIn(name,methods)
        source=(ROOT/'studio/gui/virtual_phone.py').read_text(encoding='utf-8')
        self.assertIn('guest_problem.emit',source)
        self.assertIn("'--heap-kib'",source)


class GenuineHostV072(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe=ROOT/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')
        cls.exe=exe if exe.exists() else None

    def test_real_vm_heap_and_error_line(self):
        if not self.exe:self.skipTest('Compiled host VM unavailable')
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'main.lua'
            source.write_text('assert(engine.heap_used()>0)\n'
                 'assert(engine.heap_peak()>=engine.heap_used())\n'
                 'function on_draw() engine.clear(65535) end\n')
            for kib in ('96','192','384'):
                with self.subTest(heap=kib):
                    p=subprocess.run([str(self.exe),str(source),'--interactive','--heap-kib',kib],
                        input=b'TICK 33\nQUIT\n',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=6)
                    self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
                    self.assertTrue(p.stdout.startswith(b'QEFRAME 0\n'))
            source.write_text('function on_draw()\n  error("intentional gui diagnostic")\nend\n')
            p=subprocess.run([str(self.exe),str(source),'--interactive','--heap-kib','192'],
                input=b'TICK 33\n',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=6)
            self.assertNotEqual(p.returncode,0)
            self.assertIsNotNone(guest_error(p.stderr.decode(errors='replace')))

    def test_bounded_real_vm_rejects_unexpected_heap_option(self):
        if not self.exe:self.skipTest('Compiled host VM unavailable')
        for bad in ('0','9999','192x','-1'):
            p=subprocess.run([str(self.exe),'not-a-script','--interactive','--heap-kib',bad],
                input=b'',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=4)
            self.assertEqual(p.returncode,2)
            self.assertIn(b'Invalid heap cap',p.stderr)

if __name__=='__main__':unittest.main()
