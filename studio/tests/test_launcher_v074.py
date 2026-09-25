"""v0.7.4 safe update, atomic rollback and post-update GUI regression.

All updater cases use temp roots and mocked pip: never download/alter host venv.
The final real Qt test is explicitly SKIPPED when PySide6 is unavailable.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import safe_runtime_update as updates
from tools import studio_launcher as launcher


class SafeUpdateTests(unittest.TestCase):
    def source(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='qeapp-safe-test-')
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root/'requirements-studio.txt').write_text('PySide6>=6.6,<7\n', encoding='utf-8')
        (root/'.venv').mkdir()
        return root

    def reporter(self, root):
        return launcher.Reporter(root/'logs'/'launcher.log')

    def test_pointer_never_accepts_traversal_or_external_path(self):
        root = self.source()
        for value in ('../../tmp', '/tmp/malicious', '.qeapp_envs/../evil',
                      '.qeapp_envs/../../evil', 'C:\\System32', '.qeapp_envs/x/y'):
            self.assertFalse(updates.permitted_relative(value))
            with self.assertRaises(ValueError):
                updates.runtime_directory(root, value)
        self.assertTrue(updates.permitted_relative('.venv'))
        self.assertTrue(updates.permitted_relative('.qeapp_envs/env-20260925t123456-1234'))

    def test_atomic_activation_keeps_previous_env_and_validates_corrupt_pointer(self):
        root = self.source()
        (root/'.qeapp_envs'/'env-first').mkdir(parents=True)
        updates.atomic_pointer(root, '.qeapp_envs/env-first', '.venv', reason='test')
        data = updates.load_pointer(root)
        self.assertEqual(data['active'], '.qeapp_envs/env-first')
        self.assertEqual(data['previous'], '.venv')
        self.assertTrue((root/'.venv').exists())
        self.assertFalse((root/'logs'/'active-runtime.pending.json').exists())
        (root/'logs'/'active-runtime.json').write_text('{broken json', encoding='utf-8')
        self.assertEqual(updates.load_pointer(root), {})

    def test_path_symlink_escape_is_rejected(self):
        root = self.source()
        with tempfile.TemporaryDirectory() as external:
            (root/'.qeapp_envs').mkdir()
            try: (root/'.qeapp_envs'/'env-trap').symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError): self.skipTest('Symlink unavailable')
            with self.assertRaises(ValueError):
                updates.runtime_directory(root, '.qeapp_envs/env-trap')

    def test_only_generated_failed_stage_is_cleaned(self):
        root = self.source()
        base = root/'.venv'
        (base/'keep-this').write_text('project preservation', encoding='utf-8')
        stage = root/'.qeapp_envs'/'env-generated'
        stage.mkdir(parents=True)
        (stage/'pip-incomplete').write_text('bad', encoding='utf-8')
        updates.cleanup_failed_stage(root, '.venv')
        self.assertTrue(base.exists())
        updates.cleanup_failed_stage(root, '.qeapp_envs/env-generated')
        self.assertFalse(stage.exists())
        self.assertEqual((base/'keep-this').read_text(), 'project preservation')

    def test_update_lock_prevents_overlapping_venv_promotions(self):
        root = self.source()
        with updates.update_lock(root):
            with self.assertRaises(updates.UpdateLocked):
                with updates.update_lock(root): pass
        self.assertFalse((root/'logs'/'runtime-update.lock').exists())

    def patches(self, root, healthy_results, *, pip_code=0):
        # Stable mocks prove control flow without PyPI, Windows or real Qt.
        import contextlib
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(launcher, 'ROOT', root))
        stack.enter_context(patch.object(launcher, 'REQUIREMENTS', root/'requirements-studio.txt'))
        stack.enter_context(patch.object(launcher, 'UPDATE_STATE', root/'logs'/'dependency-update-state.json'))
        stack.enter_context(patch.object(launcher, 'runtime_is_healthy', side_effect=healthy_results))
        stack.enter_context(patch.object(launcher, 'auto_update_due', return_value=(True,'daily due')))
        stack.enter_context(patch.object(launcher, 'is_venv_working', return_value=True))
        stack.enter_context(patch.object(launcher, 'ensure_pip'))
        stack.enter_context(patch.object(launcher, '_pip_install', return_value=pip_code))
        def fake_run(cmd, *_args, **_kwargs):
            if '-m' in cmd and 'venv' in cmd:
                Path(cmd[-1]).mkdir(parents=True)
            return 0
        stack.enter_context(patch.object(launcher, 'run', side_effect=fake_run))
        return stack

    def test_promotes_only_after_staged_gui_pass_and_keeps_old(self):
        root = self.source()
        (root/'.venv'/'original').write_text('before upgrade')
        self.patches(root, [True, True])
        dest, promoted = launcher.safe_preflight(launcher.python_in_venv(root/'.venv'),
                                                '.venv', launcher.Options(update_now=True),
                                                self.reporter(root))
        self.assertTrue(promoted)
        ptr = updates.load_pointer(root)
        self.assertEqual(ptr['previous'], '.venv')
        self.assertIn('.qeapp_envs', ptr['active'])
        self.assertTrue(dest.parent.parent.exists())
        self.assertEqual((root/'.venv'/'original').read_text(), 'before upgrade')
        state = json.loads((root/'logs'/'dependency-update-state.json').read_text())
        self.assertGreater(state['last_success_epoch'], 0)

    def test_failed_pip_keeps_existing_working_gui_and_pointer(self):
        root = self.source()
        updates.atomic_pointer(root, '.venv', None, reason='baseline')
        self.patches(root, [True], pip_code=2)
        base = launcher.python_in_venv(root/'.venv')
        selected, promoted = launcher.safe_preflight(base, '.venv', launcher.Options(update_now=True),
                                                     self.reporter(root))
        self.assertEqual(selected, base)
        self.assertFalse(promoted)
        self.assertEqual(updates.load_pointer(root)['active'], '.venv')
        self.assertEqual(list((root/'.qeapp_envs').glob('env-*')), [])

    def test_staged_gui_crash_keeps_old_installed_env(self):
        root = self.source()
        self.patches(root, [True, False])
        base = launcher.python_in_venv(root/'.venv')
        selected, promoted = launcher.safe_preflight(base, '.venv', launcher.Options(update_now=True),
                                                     self.reporter(root))
        self.assertEqual(selected, base)
        self.assertFalse(promoted)
        self.assertEqual(updates.load_pointer(root), {})
        self.assertEqual(list((root/'.qeapp_envs').glob('env-*')), [])

    def test_no_healthy_previous_runtime_failed_update_is_fatal(self):
        root = self.source()
        self.patches(root, [False, False])
        with self.assertRaises(launcher.LaunchError):
            launcher.safe_preflight(launcher.python_in_venv(root/'.venv'), '.venv',
                                    launcher.Options(), self.reporter(root))
        self.assertEqual(updates.load_pointer(root), {})

    def test_gui_check_readonly_never_downloads_or_stages(self):
        root = self.source()
        self.patches(root, [True])
        base = launcher.python_in_venv(root/'.venv')
        selected, promoted = launcher.safe_preflight(base, '.venv',
                                                     launcher.Options(check_only=True,gui_check=True),
                                                     self.reporter(root))
        self.assertEqual(selected, base)
        self.assertFalse(promoted)
        self.assertFalse((root/'.qeapp_envs').exists())

    def test_rollback_verifies_previous_before_switch_and_no_source_delete(self):
        root = self.source()
        (root/'.qeapp_envs'/'env-good').mkdir(parents=True)
        updates.atomic_pointer(root, '.qeapp_envs/env-good', '.venv', reason='tested')
        with (patch.object(launcher, 'ROOT', root),
              patch.object(launcher, 'REQUIREMENTS', root/'requirements-studio.txt'),
              patch.object(launcher, 'UPDATE_STATE', root/'logs'/'dependency-update-state.json'),
              patch.object(launcher, 'runtime_is_healthy', side_effect=[False,True])):
            with self.assertRaises(launcher.LaunchError):
                launcher.rollback_runtime(self.reporter(root))
            self.assertEqual(updates.load_pointer(root)['active'], '.qeapp_envs/env-good')
            selected = launcher.rollback_runtime(self.reporter(root))
            self.assertEqual(selected, launcher.python_in_venv(root/'.venv'))
            self.assertEqual(updates.load_pointer(root)['active'], '.venv')
            self.assertEqual(updates.load_pointer(root)['previous'], '.qeapp_envs/env-good')
            self.assertTrue((root/'.qeapp_envs'/'env-good').exists())

    def test_readonly_flag_cannot_accidentally_perform_rollback(self):
        root = self.source()
        (root/'run_studio.py').write_text('pass\n', encoding='utf-8')
        updates.atomic_pointer(root, '.venv', '.qeapp_envs/env-old', reason='test')
        with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'REQUIREMENTS', root/'requirements-studio.txt'):
            code = launcher.main(['--rollback-update', '--check-only'])
        self.assertEqual(code, 2)
        self.assertEqual(updates.load_pointer(root)['active'], '.venv')

    def test_post_update_test_calls_actual_script_in_child_with_offscreen(self):
        root = self.source()
        with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'run', return_value=0) as run:
            ok = launcher.post_update_gui_check(Path(sys.executable), self.reporter(root),
                                                screenshot=True, label='stage-abc')
        self.assertTrue(ok)
        cmd = [str(c) for c in run.call_args.args[0]]
        self.assertIn('tools/gui_post_update_check.py', cmd)
        self.assertIn('--screenshot', cmd)
        self.assertEqual(run.call_args.kwargs['env']['QT_QPA_PLATFORM'], 'offscreen')
        self.assertNotIn('QT_PLUGIN_PATH', run.call_args.kwargs['env'])

    def test_script_fails_closed_if_real_qt_is_not_available(self):
        if importlib.util.find_spec('PySide6'):
            self.skipTest('Actual Qt present: separate real GUI test covers success')
        root = self.source()
        report = root/'failure.json'
        p = subprocess.run([sys.executable, 'tools/gui_post_update_check.py', '--output',str(report)],
                           capture_output=True, text=True, timeout=15)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(json.loads(report.read_text())['status'], 'FAIL')
        self.assertIn('ModuleNotFoundError', p.stdout)

    @unittest.skipUnless(importlib.util.find_spec('PySide6'),
                         'PySide6 not installed here: REAL Qt window test NOT RUN')
    def test_actual_qt_window_paint_and_temp_project(self):
        from tools.gui_post_update_check import probe
        report = probe()
        self.assertEqual(report['status'], 'PASS', report)
        self.assertIn('Temporary project Explorer, editor and device switching', report['tests'])


if __name__ == '__main__':
    unittest.main()
