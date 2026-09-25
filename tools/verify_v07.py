#!/usr/bin/env python3
"""QEAPP Studio v0.7 host validation. Hardware and GUI gates remain explicit."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from studio_firmware import firmware_root
import time

ROOT=Path(__file__).resolve().parents[1]

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system-lua',action='store_true',help='Diagnostic system Lua on Linux host only')
    p.add_argument('--require-qt',action='store_true',help='Fail without executed PySide6 tests')
    p.add_argument('--full',action='store_true',help='Also run v0.5 legacy regression suite')
    p.add_argument('--report',type=Path,default=ROOT/'build/reports/v07/verification.json')
    args=p.parse_args()
    has_qt=importlib.util.find_spec('PySide6') is not None
    report={'version':'0.7.0', 'scope':'PC host only',
            'pyside6_gui':'EXECUTED_BY_UNIT_SUITE' if has_qt else 'NOT_TESTED',
            'esp32_platformio':'NOT_RUN', 'physical_esp32':'NOT_RUN',
            'signed_device_install':'NOT_RUN', 'signing_checks':'UNIT_SUITE_WITH_TEMPORARY_TEST_KEY',
            'checks':[]}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    def run(name, command, timeout=150):
        begin=time.monotonic()
        try:
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=timeout,
                             env={**os.environ,'PYTHONUTF8':'1','QT_QPA_PLATFORM':'offscreen',
                                  'QEAPP_FIRMWARE_ROOT':os.environ.get(
                                     'QEAPP_FIRMWARE_ROOT',str(firmware_root() or ''))})
            status='PASS' if r.returncode==0 else 'FAIL'
            excerpt='\n'.join((r.stdout+'\n'+r.stderr).splitlines()[-24:])
        except (OSError,subprocess.TimeoutExpired) as exc:
            status='FAIL';excerpt=str(exc)
        report['checks'].append({'name':name,'status':status,
                        'elapsed_s':round(time.monotonic()-begin,3),'evidence':excerpt})
        print(status,name,flush=True)
        return status=='PASS'
    ok=run('python-compileall',[sys.executable,'-m','compileall','-q','studio','tools'])
    ok=run('build-genuine-host-vm',[sys.executable,'tools/build_lua_host.py']+
            (['--system-lua'] if args.system_lua else []),timeout=180) and ok
    if ok:
        ok=run('v07-studio-unit-optional-Qt',[sys.executable,'-m','unittest','discover',
            '-s','studio/tests','-v'],timeout=110) and ok
        ok=run('legacy-host-unit-tests',[sys.executable,'-m','unittest','discover',
            '-s','tests','-v'],timeout=220) and ok
        ok=run('real-vm-30-frame-metrics-png',[sys.executable,'tools/virtual_phone_cli.py',
            'projects/lua-snake/main.lua','-o',str(args.report.parent/'snake-host.png'),
            '--frames','30'],timeout=80) and ok
    if args.full:
        ok=run('v05-full-regression',[sys.executable,'tools/verify_v05.py']+
           (['--system-lua'] if args.system_lua else []),timeout=360) and ok
    if not has_qt:
        report['checks'].append({'name':'qt-offscreen-ui','status':'NOT_RUN',
                                 'evidence':'PySide6 missing on validation host'})
        if args.require_qt:ok=False
    report['result']='HOST_PASS_GUI_UNTESTED' if ok and not has_qt else 'PASS' if ok else 'FAIL'
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('RESULT',report['result'],'\nREPORT',args.report)
    return 0 if ok else 2
if __name__=='__main__':sys.exit(main())
