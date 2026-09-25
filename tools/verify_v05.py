#!/usr/bin/env python3
"""QEAPP Studio v0.5 reproducible host gate (never a real ESP32 target gate)."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from studio_firmware import firmware_root

ROOT = Path(__file__).resolve().parents[1]
FW = firmware_root()

def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--system-lua', action='store_true', help='Diagnostic shared liblua fallback; not official firmware library')
    a.add_argument('--require-qt', action='store_true', help='Fail if GUI offscreen tests cannot run')
    a.add_argument('--firmware-regression', action='store_true', help='Run slow v2.4.2 host firmware regression suite')
    a.add_argument('--report-dir', type=Path, default=ROOT / 'build/reports/v05')
    args = a.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    has_qt = importlib.util.find_spec('PySide6') is not None
    env = os.environ.copy()
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    if FW is not None: env['QEAPP_FIRMWARE_ROOT'] = str(FW)
    if has_qt:
        env['QT_QPA_PLATFORM'] = 'offscreen'
    stages = []

    def stage(name: str, command: list[str], timeout=180):
        print('RUN:', name, flush=True)
        try:
            p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
            rc, output = p.returncode, p.stdout + '\n' + p.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            rc, output = 124, f'{type(exc).__name__}: {exc}'
        logname = re.sub(r'[^a-zA-Z0-9-]', '-', name) + '.log'
        (args.report_dir / logname).write_text(output, encoding='utf-8')
        count = re.search(r'Ran (\d+) tests?', output)
        skipped = re.search(r'OK \(skipped=(\d+)\)', output)
        item = {'stage': name, 'status': 'PASS' if rc == 0 else 'FAIL',
                'exit': rc, 'tests': int(count.group(1)) if count else None,
                'skipped': int(skipped.group(1)) if skipped else 0, 'log': logname}
        stages.append(item)
        print(item['status'], name, flush=True)
        return rc == 0

    build = [sys.executable, 'tools/build_lua_host.py']
    if args.system_lua: build.append('--system-lua')
    if stage('host-lua-build', build):
        stage('unit-game-signature-sprite', [sys.executable,'-m','unittest','discover','-s','tests','-v'])
        stage('unit-studio-security', [sys.executable,'-m','unittest','discover','-s','studio/tests','-v'])
        if FW is not None: stage('firmware-beta-mock-link', [sys.executable, 'tools/test_lua_beta_host.py'], timeout=160)
        else: print('SKIP firmware-beta-mock-link: separate VQEAF-OS checkout not installed')
        stage('sprite-preview', [sys.executable,'tools/lua_preview.py','projects/lua-sprite/main.lua',
              '--frames','30', '-o', str(args.report_dir / 'sprite_preview_240x320.png')], timeout=30)
    if args.firmware_regression:
        if FW is None: a.error('--firmware-regression requires QEAPP_FIRMWARE_ROOT')
        stage('firmware-v242-regression', [sys.executable,str(FW/'tools/verify_v242.py')],timeout=300)
    good = all(e['status']=='PASS' for e in stages)
    for item in stages:
        if item['stage']=='unit-game-signature-sprite' and item['skipped']:
            good = False # real signer must run in this suite
        if item['stage']=='unit-studio-security' and item['skipped'] and has_qt:
            good = False # unexpected Qt skip on Qt-enabled host
    if args.require_qt and not has_qt: good = False
    state = 'HOST_PASS_GUI_UNTESTED' if good and not has_qt else 'HOST_PASS' if good else 'FAIL'
    screenshot = args.report_dir/'sprite_preview_240x320.png'
    info = {'version':'0.5.0','checked_utc':datetime.now(timezone.utc).isoformat(),
            'status':state, 'qt_installed':has_qt, 'source':
            'SYSTEM_LUA_DIAGNOSTIC' if args.system_lua else 'OFFICIAL_LUA_SOURCE',
            'real_target_platformio':'NOT_RUN','device_hardware':'NOT_TESTED','stages':stages,
            'preview_sha256':hashlib.sha256(screenshot.read_bytes()).hexdigest() if screenshot.exists() else None}
    (args.report_dir/'result.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    lines=['# QEAPP Studio v0.5 host verification', '',f'Overall: **{state}**','',
        'PySide6 GUI test: **'+('OFFSCREEN TESTED' if has_qt and good else 'UNTESTED / SKIPPED' if not has_qt else 'FAILED')+'**.',
        'ESP32-S3 PlatformIO build and hardware: **NOT RUN**.',
        'Lua source: **'+info['source']+'**.','',
        '| Stage | Status | Cases | Skipped |','|---|---|---:|---:|']
    for s in stages:lines.append(f"| {s['stage']} | {s['status']} | {s['tests'] or '—'} | {s['skipped']} |")
    lines.extend(['','SHA-256 preview: `'+str(info['preview_sha256'])+'`.',''])
    (args.report_dir/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    print('REPORT:',args.report_dir/'report.md')
    return 0 if good else 1

if __name__=='__main__':raise SystemExit(main())
