"""Offline unit tests for v0.7.3 Windows dependency auto-update lifecycle.

No downloads, GUI or real project folders are changed by this test module.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import studio_launcher as launcher


class AutoUpdateTests(unittest.TestCase):
    def reporter(self, folder):
        return launcher.Reporter(Path(folder) / 'launcher.log')

    def test_missing_pip_is_recovered_using_bundled_ensurepip(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(launcher, 'run', side_effect=[1, 0, 0]) as run:
                launcher.ensure_pip(Path(sys.executable), launcher.Options(), self.reporter(d))
                self.assertEqual(run.call_count, 3)
                self.assertEqual(run.call_args_list[1].args[0][2], 'ensurepip')

    def test_missing_pip_offline_stops_without_ensurepip(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(launcher, 'run', return_value=1) as run:
                with self.assertRaises(launcher.LaunchError):
                    launcher.ensure_pip(Path(sys.executable), launcher.Options(offline=True),
                                        self.reporter(d))
                run.assert_called_once()

    def test_first_launch_schedules_update(self):
        due, reason = launcher.auto_update_due(Path(sys.executable), launcher.Options(),
                                                now=100_000.0, state={})
        self.assertTrue(due)
        self.assertIn('new environment', reason)

    def test_no_repeated_network_call_within_day(self):
        python = Path(sys.executable)
        state = {**launcher._update_key(python), 'last_success_epoch': 100_000.0,
                 'last_attempt_epoch': 100_000.0}
        due, reason = launcher.auto_update_due(python, launcher.Options(),
                                                now=101_000.0, state=state)
        self.assertFalse(due)
        self.assertIn('<24 h', reason)
        due, _ = launcher.auto_update_due(python, launcher.Options(),
                                          now=100_000 + launcher.AUTO_UPDATE_INTERVAL_S + 1,
                                          state=state)
        self.assertTrue(due)

    def test_failed_update_backoff_keeps_working_gui_available(self):
        python = Path(sys.executable)
        state = {**launcher._update_key(python), 'last_success_epoch': 10.0,
                 'last_attempt_epoch': 100_000.0}
        due, why = launcher.auto_update_due(python, launcher.Options(),
                                             now=101_000.0, state=state)
        self.assertFalse(due)
        self.assertIn('failure', why)
        due, _ = launcher.auto_update_due(python, launcher.Options(),
                                          now=100_000 + launcher.AUTO_UPDATE_RETRY_S + 1,
                                          state=state)
        self.assertTrue(due)

    def test_offline_no_update_readonly_and_system_never_upgrade_implicitly(self):
        for options in (launcher.Options(offline=True), launcher.Options(no_update=True),
                        launcher.Options(check_only=True), launcher.Options(no_install=True),
                        launcher.Options(system=True)):
            self.assertFalse(launcher.auto_update_due(Path(sys.executable), options,
                                                      state={})[0])
        self.assertTrue(launcher.auto_update_due(Path(sys.executable),
                                                launcher.Options(system=True, update_now=True),
                                                state={})[0])

    def test_requirements_hash_or_python_change_invalidates_cache(self):
        python = Path(sys.executable)
        state = {**launcher._update_key(python), 'last_success_epoch': 10_000.0,
                 'last_attempt_epoch': 10_000.0}
        state['requirements_sha256'] = 'changed'
        due, why = launcher.auto_update_due(python, launcher.Options(), now=10_001.0,
                                             state=state)
        self.assertTrue(due)
        self.assertIn('requirements', why)

    def test_update_state_corruption_is_ignored_and_atomic_save(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'state.json'
            path.write_text('{ bad json', encoding='utf-8')
            self.assertEqual(launcher.load_update_state(path), {})
            launcher.save_update_state({'last_success_epoch': 123}, self.reporter(d), path)
            self.assertEqual(json.loads(path.read_text())['last_success_epoch'], 123)
            self.assertFalse(path.with_suffix('.pending.json').exists())

    def test_automatic_update_succeeds_then_qt_smoke(self):
        with tempfile.TemporaryDirectory() as d:
            with (patch.object(launcher, '_probe_versions', return_value=True),
                  patch.object(launcher, '_pip_check', return_value=True),
                  patch.object(launcher, 'auto_update_due', return_value=(True, 'due')),
                  patch.object(launcher, '_pip_install', return_value=0) as pip,
                  patch.object(launcher, 'gui_smoke', return_value=True) as smoke,
                  patch.object(launcher, 'save_update_state') as save,
                  patch.object(launcher, 'load_update_state', return_value={})):
                launcher.preflight(Path(sys.executable), launcher.Options(), self.reporter(d))
                pip.assert_called_once()
                self.assertTrue(pip.call_args.kwargs['upgrade'])
                smoke.assert_called_once()
                self.assertEqual(save.call_count, 2)  # attempted and successful

    def test_failed_online_check_continues_if_local_installation_is_healthy(self):
        with tempfile.TemporaryDirectory() as d:
            with (patch.object(launcher, '_probe_versions', return_value=True),
                  patch.object(launcher, '_pip_check', return_value=True),
                  patch.object(launcher, 'auto_update_due', return_value=(True, 'due')),
                  patch.object(launcher, '_pip_install', return_value=1) as pip,
                  patch.object(launcher, 'gui_smoke', return_value=True) as smoke,
                  patch.object(launcher, 'save_update_state'),
                  patch.object(launcher, 'load_update_state', return_value={})):
                launcher.preflight(Path(sys.executable), launcher.Options(), self.reporter(d))
                pip.assert_called_once()
                smoke.assert_called_once()

    def test_missing_dependencies_auto_installs_before_launch(self):
        with tempfile.TemporaryDirectory() as d:
            with (patch.object(launcher, '_probe_versions', side_effect=[False, True, True]),
                  patch.object(launcher, '_pip_check', return_value=True),
                  patch.object(launcher, '_pip_install', return_value=0) as pip,
                  patch.object(launcher, 'gui_smoke', return_value=True)):
                launcher.preflight(Path(sys.executable), launcher.Options(), self.reporter(d))
                self.assertTrue(pip.call_args.kwargs['upgrade'])

    def test_pip_check_mismatch_auto_repairs(self):
        with tempfile.TemporaryDirectory() as d:
            with (patch.object(launcher, '_probe_versions', return_value=True),
                  patch.object(launcher, '_pip_check', side_effect=[False, True, True]),
                  patch.object(launcher, '_pip_install', return_value=0) as pip,
                  patch.object(launcher, 'gui_smoke', return_value=True)):
                launcher.preflight(Path(sys.executable), launcher.Options(), self.reporter(d))
                pip.assert_called_once()

    def test_offline_missing_package_fails_without_network_or_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            with (patch.object(launcher, '_probe_versions', return_value=False),
                  patch.object(launcher, '_pip_install') as pip,
                  patch.object(launcher, 'gui_smoke') as qt):
                with self.assertRaises(launcher.LaunchError):
                    launcher.preflight(Path(sys.executable), launcher.Options(offline=True),
                                       self.reporter(d))
                pip.assert_not_called()
                qt.assert_not_called()

    def test_pip_invocation_no_shell_and_network_has_short_retry(self):
        with tempfile.TemporaryDirectory() as d, patch.object(launcher, 'run', return_value=0) as run:
            self.assertEqual(launcher._pip_install(Path(sys.executable), self.reporter(d),
                                                   upgrade=True), 0)
            argv, _ = run.call_args.args
            self.assertEqual(argv[:4], [Path(sys.executable), '-m', 'pip', 'install'])
            self.assertIn('--upgrade', argv)
            self.assertEqual(run.call_args.kwargs['env']['PIP_RETRIES'], '1')
            self.assertEqual(run.call_args.kwargs['env']['PIP_NO_INPUT'], '1')

    def test_batch_launch_arguments_and_python_path_are_quoted(self):
        src = (Path(__file__).resolve().parents[2] / 'run_studio.bat').read_text()
        self.assertIn('"%QEAPP_BOOT_PY%" -B tools\\studio_launcher.py %*', src)
        self.assertIn('set "QEAPP_EXIT=%ERRORLEVEL%"', src)
        self.assertNotIn('set "PY=py -3"', src)


if __name__ == '__main__':
    unittest.main()
