#!/usr/bin/env python3
"""Reproducible v0.7.2 tests; no silent GUI/device PASS claims."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from studio_firmware import firmware_root
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system-lua',action='store_true',help='Linux PC diagnosis only; NOT release Lua source')
    p.add_argument('--require-qt',action='store_true',help='Fail if actual offscreen Qt tests cannot execute')
    p.add_argument('--full',action='store_true',help='Also run slow legacy host regression suite')
    p.add_argument('--out',type=Path,default=ROOT/'build/reports/v072')
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'QEAPP_FIRMWARE_ROOT':str(firmware_root() or ''),
         'QT_QPA_PLATFORM':'offscreen','PYTHONUTF8':'1'}
    if a.system_lua: env['QEAPP_HOST_SYSTEM_LUA']='1'
    has_qt=importlib.util.find_spec('PySide6') is not None
    report={'version':'0.7.2','checked_utc':datetime.now(timezone.utc).isoformat(),
            'runtime':'SYSTEM_LUA_DIAGNOSTIC' if a.system_lua else 'OFFICIAL_HASH_VERIFIED_LUA_EXPECTED',
            'gui_pyside6':'OFFSCREEN_TEST_EXECUTED' if has_qt else 'NOT_TESTED_NO_QT',
            'device_hardware':'NOT_TESTED','platformio':'NOT_RUN',
            'signed_install_on_physical_device':'NOT_RUN','checks':[]}
    def run(name,argv,timeout=160):
        start=time.monotonic()
        try:
            r=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=timeout)
            code=r.returncode; output=(r.stdout+'\n'+r.stderr)[-6000:]
        except (OSError,subprocess.TimeoutExpired) as exc:
            code=124;output=f'{type(exc).__name__}: {exc}'
        report['checks'].append({'name':name,'status':'PASS' if code==0 else 'FAIL',
            'elapsed_s':round(time.monotonic()-start,2),'evidence':output})
        print(('PASS' if code==0 else 'FAIL'),name,flush=True)
        return code==0
    # Mutually independent stages, so a failing VM doesn't hide unrelated GUI failures.
    built=run('python-compileall',[sys.executable,'-m','compileall','-q','studio','tools'])
    doctor=run('doctor-readonly',[sys.executable,'tools/studio_doctor.py','--json'])
    if not built: report['checks'].append({'name':'unit-tests','status':'NOT_RUN','evidence':'compileall failed'})
    vm=run('real-host-vm-build',[sys.executable,'tools/build_lua_host.py']+
           (['--system-lua'] if a.system_lua else []),timeout=240)
    unit=run('studio-tests-qt-optional',[sys.executable,'-m','unittest','discover','-s','studio/tests','-v'],timeout=120)
    legacy=run('core-signer-regression',[sys.executable,'-m','unittest','discover','-s','tests','-v'],timeout=220)
    if vm:
        run('real-host-vm-60-frame-png',[sys.executable,'tools/virtual_phone_cli.py',
            'projects/lua-snake/main.lua','-o',str(a.out/'host-snake-60.png'),'--frames','60'],timeout=90)
    if a.full:
        run('legacy-v05-full-host-gate',[sys.executable,'tools/verify_v05.py']+
           (['--system-lua'] if a.system_lua else []),timeout=500)
    if not has_qt:
        report['checks'].append({'name':'GUI-Qt-offscreen','status':'NOT_RUN',
                                 'evidence':'PySide6 not installed; static compilation is NOT GUI execution'})
    # The C++ host tests can pass while Windows GUI remains unverified. Explicit status.
    ok=all(c['status']!='FAIL' for c in report['checks']) and vm and unit and legacy and built and doctor
    if a.require_qt and not has_qt:ok=False
    report['result']=('FAIL' if not ok else 'HOST_PASS_GUI_UNTESTED' if not has_qt else 'HOST_PASS_QT_OFFSCREEN')
    (a.out/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    lines=['# QEAPP Studio v0.7.2 — verification','',
           f'Overall: **{report["result"]}**',
           f'Runtime source: **{report["runtime"]}**',
           'Physical ESP32-S3 / firmware packaging + installation / Serial 115200: **NOT RUN**.','',
           '| Check | Result |','|---|---|']
    lines += [f'| {c["name"]} | {c["status"]} |' for c in report['checks']]
    lines += ['', 'See `verification.json` for full captured evidence.', '']
    (a.out/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    print('RESULT:',report['result'],'\nREPORT:',a.out/'report.md')
    return 0 if ok else 2

if __name__=='__main__':raise SystemExit(main())
