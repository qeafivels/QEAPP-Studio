#!/usr/bin/env python3
"""Real, isolated Qt widget post-update probe. Never changes a user's project.

Exit 0 means a Qt QApplication and the actual StudioWindow were constructed,
painted offscreen and accepted a temporary project. No device/Windows claim.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def probe(*, screenshot: Path | None = None) -> dict:
    started = time.monotonic()
    result = {'schema': 1, 'status': 'FAIL', 'phase': 'start', 'tests': [],
              'platform': 'offscreen', 'screenshot': None}
    # Keep user configuration and existing projects entirely out of the smoke test.
    with tempfile.TemporaryDirectory(prefix='qeapp-gui-probe-') as scratch:
        os.environ['APPDATA'] = scratch
        os.environ['XDG_CONFIG_HOME'] = scratch
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        os.environ.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None)
        os.environ.pop('QT_PLUGIN_PATH', None)
        app = None
        window = None
        old_hook = sys.excepthook
        callback_errors = []
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QImage
            from PIL import Image
            from cryptography.hazmat.primitives.asymmetric import ec
            app = QApplication.instance() or QApplication([])
            assert app.platformName().lower() == 'offscreen', app.platformName()
            assert ec.SECP256R1().name == 'secp256r1'
            assert Image.new('RGB', (1, 1)).size == (1, 1)
            result['tests'].append('Qt, Pillow and cryptography import/initialization')
            result['phase'] = 'window'
            def exception_capture(exc_type, exc, tb):
                callback_errors.append(''.join(traceback.format_exception_only(exc_type, exc))[:350])
            sys.excepthook = exception_capture
            from studio.gui.window import StudioWindow
            window = StudioWindow()
            window.show()
            app.processEvents()
            assert window.isVisible()
            assert 'QEAPP Studio' in window.windowTitle()
            assert window.left_pages.count() == 2
            assert window.tabs.count() == 0
            assert window.device.screen.width() == 240
            assert window.device.screen.height() == 320
            assert window.device.last_image is not None
            result['tests'].append('Real StudioWindow layout, editor and 240x320 RGB display')
            result['phase'] = 'project'
            from tools.qstudio import init_project
            tmp_project = Path(scratch) / 'validation-project'
            init_project('text', tmp_project, 'validation', 'Probe')
            window._set_project(tmp_project)
            window.open_document('content.txt')
            app.processEvents()
            assert 'content.txt' in window.editors
            assert window.tabs.count() == 1
            assert window.tree.topLevelItemCount() > 0
            window.show_project_search()
            app.processEvents()
            assert window.left_pages.currentIndex() == 1
            window.show_virtual_phone()
            app.processEvents()
            assert window.device.last_image.width() == 240
            assert window.device.last_image.height() == 320
            result['tests'].append('Temporary project Explorer, editor and device switching')
            result['phase'] = 'paint'
            # Qt must actually paint; a successful widget import is not enough.
            img = window.grab().toImage()
            assert not img.isNull() and img.width() >= 900 and img.height() >= 600
            if screenshot is not None:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                assert img.save(str(screenshot), 'PNG')
                result['screenshot'] = str(screenshot)
            assert not callback_errors, '; '.join(callback_errors)
            result['tests'].append('Qt offscreen window render, event-loop and no callback exceptions')
            result['phase'] = 'done'
            result['status'] = 'PASS'
        except BaseException as exc:
            result['error'] = type(exc).__name__ + ': ' + str(exc)[:350]
        finally:
            sys.excepthook = old_hook
            if window is not None:
                try:
                    window.close()
                    if app is not None: app.processEvents()
                except Exception as exc:
                    result['status'] = 'FAIL'
                    result['error'] = 'Window close failed: ' + str(exc)[:200]
            if app is not None:
                try: app.quit()
                except Exception: pass
    result['elapsed_ms'] = round(1000 * (time.monotonic() - started), 1)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write bounded diagnostic JSON')
    parser.add_argument('--screenshot', type=Path, help='Actual offscreen Qt screenshot path')
    args = parser.parse_args(argv)
    report = probe(screenshot=args.screenshot)
    print(f"GUI POST-UPDATE {report['status']}: {report['phase']} ({report['elapsed_ms']}ms)")
    if report.get('error'):
        print('ERROR:', report['error'])
    for check in report['tests']:
        print('PASS:', check)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_suffix('.pending.json')
        temp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, args.output)
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
