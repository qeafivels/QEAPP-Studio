"""Pure-stdlib tests; runnable even on hosts without PySide6 or Windows CMD."""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import studio_launcher as l


class LauncherTests(unittest.TestCase):
    def test_release_version_prefix(self):
        self.assertEqual(l.version_tuple('6.9.2'), (6, 9, 2))
        self.assertEqual(l.version_tuple('41.0.0rc2'), (41, 0, 0))
        self.assertEqual(l.version_tuple('foo'), ())

    def test_missing_outdated_and_future_major_dependencies(self):
        versions = {'PySide6': '6.5.1', 'cryptography': '41.0', 'Pillow': '9.5'}
        errors = l.missing_dependencies(lambda package: versions[package])
        self.assertEqual(len(errors), 2)
        self.assertIn('PySide6', errors[0])
        self.assertIn('Pillow', errors[1])
        versions.update({'PySide6': '6.10', 'Pillow': '12.0'})
        self.assertFalse(l.missing_dependencies(lambda package: versions[package]))
        versions.update({'PySide6': '7.0.0'})
        self.assertEqual(len(l.missing_dependencies(lambda package: versions[package])), 1)

    def test_missing_package_in_metadata(self):
        def fail(package):
            if package == 'Pillow':
                raise PackageNotFoundError(package)
            return '99.0' if package == 'cryptography' else '6.9.0'
        errors = l.missing_dependencies(fail)
        self.assertEqual(errors, ['Pillow: not installed'])

    def test_check_only_never_creates_venv(self):
        with tempfile.TemporaryDirectory() as d:
            r = l.Reporter(Path(d) / 'test.log')
            with patch.object(l, 'VENV', Path(d) / '.venv'), patch.object(l, 'run') as command:
                with self.assertRaisesRegex(l.LaunchError, 'No .venv'):
                    l.ensure_python(l.Options(check_only=True), r)
                command.assert_not_called()

    def test_existing_broken_venv_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as d:
            venv = Path(d) / '.venv'
            exe = l.python_in_venv(venv)
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b'not an executable')
            with patch.object(l, 'VENV', venv), patch.object(l, 'is_venv_working', return_value=False):
                with self.assertRaisesRegex(l.LaunchError, 'Rename'):
                    l.ensure_python(l.Options(), l.Reporter(Path(d) / 'log'))
            self.assertTrue(exe.exists())

    def test_system_python_does_not_mutate_filesystem(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(l, 'VENV', Path(d) / '.venv'):
                selected = l.ensure_python(l.Options(system=True), l.Reporter(Path(d) / 'log'))
                self.assertEqual(selected, Path(sys.executable))
                self.assertFalse((Path(d) / '.venv').exists())

    def test_offscreen_probe_is_a_separate_process(self):
        envs = []
        def probe(command, reporter, **kwargs):
            envs.append(kwargs['env'])
            self.assertIn('QApplication', command[-1])
            self.assertIn('cryptography', command[-1])
            self.assertIn('PIL', command[-1])
            return 0
        with tempfile.TemporaryDirectory() as d, patch.object(l, 'run', side_effect=probe):
            self.assertTrue(l.gui_smoke(Path(sys.executable), l.Reporter(Path(d) / 'log')))
        self.assertEqual(envs[0]['QT_QPA_PLATFORM'], 'offscreen')
        self.assertNotIn('QT_QPA_PLATFORM_PLUGIN_PATH', envs[0])

    def test_no_implicit_bootstrap_or_compilation_without_lua(self):
        with tempfile.TemporaryDirectory() as d, patch.object(l, 'ROOT', Path(d)):
            with patch.object(l, 'run') as command:
                l.setup_vm(Path(sys.executable), l.Options(), l.Reporter(Path(d) / 'log'))
                command.assert_not_called()

    def test_check_only_never_pip_installs(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(l, 'run', return_value=1) as runner:
                with self.assertRaises(l.LaunchError):
                    l.preflight(Path(sys.executable), l.Options(check_only=True),
                                l.Reporter(Path(d) / 'log'))
                self.assertEqual(runner.call_count, 1)

    def test_gui_spawns_venv_interpreter_without_shell(self):
        with tempfile.TemporaryDirectory() as d, patch.object(l, 'ROOT', Path(d)):
            from unittest.mock import MagicMock
            fake = MagicMock()
            fake.__enter__.return_value.wait.return_value = 0
            with patch.object(l.subprocess, 'Popen', return_value=fake) as popen:
                self.assertEqual(l.launch_gui(Path('C:/Python Folder/python.exe'),
                                              l.Reporter(Path(d) / 'log')), 0)
                args, kwargs = popen.call_args
                self.assertIsInstance(args[0], list)
                self.assertEqual(args[0][0], 'C:/Python Folder/python.exe')
                self.assertNotIn('shell', kwargs)

    def test_logger_rotates_at_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'log.txt'
            path.write_bytes(b'x' * (1_000_001))
            reporter = l.Reporter(path)
            reporter.say('OK', 'rotated')
            self.assertTrue((Path(d) / 'log.previous.log').is_file())
            self.assertLess(path.stat().st_size, 1024)

    def test_vm_optional_does_not_block_editor(self):
        with tempfile.TemporaryDirectory() as d, patch.object(l, 'ROOT', Path(d)):
            reporter = l.Reporter(Path(d) / 'launcher.log')
            self.assertTrue(l.scan_environment(reporter, require_vm=False))
            self.assertFalse(l.scan_environment(reporter, require_vm=True))

    def test_batch_file_quotes_python_and_checks_exit_code(self):
        bat = (Path(__file__).resolve().parents[2] / 'run_studio.bat').read_text()
        self.assertIn('"%QEAPP_BOOT_PY%" -B tools\\studio_launcher.py %*', bat)
        self.assertIn('set "QEAPP_EXIT=%ERRORLEVEL%"', bat)
        self.assertIn('EnableExtensions DisableDelayedExpansion', bat)
        self.assertIn('logs\\launcher.log', bat)
        self.assertNotIn('set "PY=py -3"', bat)


if __name__ == '__main__':
    unittest.main()
