#!/usr/bin/env python3
"""M3 release preflight; Qt skipped is explicitly reported, not counted PASS."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--system-lua',action='store_true',help='Linux system Lua host-only diagnostic')
    p.add_argument('--require-qt',action='store_true',help='Fail if PySide6 GUI smoke unavailable')
    p.add_argument('--full',action='store_true',help='Run old v0.5 firmware/VM regression gate')
    p.add_argument('--report',type=Path,default=ROOT/'build/reports/v06/verification.json')
    args=p.parse_args()
    qt=importlib.util.find_spec('PySide6') is not None
    report={'release':'v0.6','qt_present':qt,'qt_gui':'NOT_TESTED' if not qt else 'TESTED_VIA_UNIT_SUITE',
            'esp32_s3':'NOT_TESTED','signed_lua_on_device':'NOT_TESTED','checks':[]}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    def run(name,cmd,timeout=180):
        started=time.monotonic()
        try:
            result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=timeout,
                                  env={**os.environ,'PYTHONUTF8':'1','QT_QPA_PLATFORM':'offscreen'})
            status='PASS' if result.returncode==0 else 'FAIL'
            evidence='\n'.join((result.stdout+'\n'+result.stderr).splitlines()[-15:])
        except (OSError, subprocess.TimeoutExpired) as err:
            status='FAIL';evidence=str(err)
        item={'name':name,'status':status,'elapsed_s':round(time.monotonic()-started,3),'evidence':evidence}
        report['checks'].append(item)
        print(status,name)
        return status=='PASS'
    okay=True
    okay&=run('python-compile',[sys.executable,'-m','py_compile','studio/gui/window.py',
        'studio/gui/virtual_phone.py','studio/core/frame_protocol.py'])
    if not qt:
        print('SKIPPED: PySide6 GUI on this machine is NOT verified.')
        if args.require_qt:okay=False
    okay&=run('build-real-lua-host',[sys.executable,'tools/build_lua_host.py']+
              (['--system-lua'] if args.system_lua else []))
    if okay:
        okay&=run('unit-studio-protocol-Qt-optional',[sys.executable,'-m','unittest',
                   'discover','-s','studio/tests','-v'],timeout=100)
        okay&=run('native-host-frame-and-PNG',[sys.executable,'tools/virtual_phone_cli.py',
                   'projects/lua-snake/main.lua','-o',str(ROOT/'build/reports/v06/virtual-phone.png'),
                   '--frames','14'],timeout=40)
    if args.full:
        okay&=run('legacy-v05-gate',[sys.executable,'tools/verify_v05.py']+
                  (['--system-lua'] if args.system_lua else []),timeout=280)
    report['result']='PASS' if okay else 'FAIL'
    args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('REPORT',args.report)
    return 0 if okay else 2
if __name__=='__main__':sys.exit(main())
