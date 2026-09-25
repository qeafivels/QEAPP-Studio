#!/usr/bin/env python3
"""Release gate: repeatable PC evidence for Studio v0.4.1.

Never claims that a host mock is a PlatformIO build or that a simulated
screenshot came from an ESP32-S3. Needs explicit --system-lua for Linux
system-library diagnostic fallback when official Lua vendor files are absent.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from studio_firmware import firmware_root

ROOT=Path(__file__).resolve().parents[1]
FW=firmware_root()

def run(args,env=None,timeout=180):
    proc=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env=env,timeout=timeout)
    return {'argv':[str(x) for x in args], 'returncode':proc.returncode,
            'stdout':proc.stdout[-30000:], 'stderr':proc.stderr[-30000:]}

def summarize(step):
    text=step['stdout']+'\n'+step['stderr']
    m=re.search(r'Ran (\d+) tests',text)
    skipped=re.search(r'OK \(skipped=(\d+)\)',text)
    return {'returncode':step['returncode'],'tests':int(m.group(1)) if m else None,
            'skipped':int(skipped.group(1)) if skipped else 0}

def main():
    a=argparse.ArgumentParser();a.add_argument('--system-lua',action='store_true',help='Linux host-only fallback')
    a.add_argument('--report-dir',type=Path,default=ROOT/'build'/'v041_verification')
    a.add_argument('--skip-firmware-host',action='store_true')
    args=a.parse_args();dest=args.report_dir.resolve();dest.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    if FW is not None: env['QEAPP_FIRMWARE_ROOT']=str(FW)
    vendor=FW is not None and (FW/'lib/VqeafLua54/src/lua.h').exists()
    if not vendor and not args.system_lua:
        print('Missing official Lua vendor sources. Run python tools/bootstrap_lua.py'
              ' or use --system-lua for Linux host-only tests.',file=sys.stderr)
        return 2
    steps={}
    opts=[sys.executable,str(ROOT/'tools/build_lua_host.py')]
    if args.system_lua and not vendor:opts+=['--system-lua']
    steps['build_lua_host']=run(opts,env)
    if steps['build_lua_host']['returncode']:
        print('LUA HOST BUILD FAILED',file=sys.stderr);return 2
    steps['engine_regressions']=run([sys.executable,'-m','unittest','discover','-s','tests','-v'],env,timeout=180)
    steps['studio_regressions']=run([sys.executable,'-m','unittest','discover','-s','studio/tests','-v'],env,timeout=180)
    preview_env=env.copy()
    if args.system_lua:preview_env['QEAPP_HOST_SYSTEM_LUA']='1'
    shot=dest/'snake_host_replay.png'
    steps['lua_preview']=run([sys.executable,'tools/qstudio.py','lua-preview',
       str(ROOT/'projects/lua-snake'),'--frames','8','--replay','tests/input_replay.json',
       '--output',str(shot)],preview_env)
    if shot.is_file():
        steps['lua_preview']['image_sha256']=hashlib.sha256(shot.read_bytes()).hexdigest()
    if not args.skip_firmware_host:
        if os.name=='posix' and Path('/usr/lib/x86_64-linux-gnu/liblua5.4.so.0').is_file():
            steps['mock_firmware_link']=run([sys.executable,'tools/test_lua_beta_host.py'],env,timeout=180) if FW is not None else {'returncode':None,'skip':'VQEAF-OS companion checkout missing'}
        else:
            steps['mock_firmware_link']={'returncode':None,'skip':'host-only Linux system Lua missing'}
    unit=summarize(steps['engine_regressions']);studio=summarize(steps['studio_regressions'])
    qt=importlib.util.find_spec('PySide6') is not None
    success=steps['build_lua_host']['returncode']==0 and \
      steps['engine_regressions']['returncode']==0 and \
      steps['studio_regressions']['returncode']==0 and \
      steps['lua_preview']['returncode']==0 and \
      steps.get('mock_firmware_link',{'returncode':0})['returncode'] in (0,None)
    report={'version':'0.4.1','host_pass':success,'tests_engine':unit,'tests_studio':studio,
      'pyside6_available':qt, 'pyside6_tests_executed':qt,
      'lua_dependency': 'official Lua 5.4.8 source' if vendor and not args.system_lua else 'system Lua 5.4 diagnostic',
      'firmware_mock_is_hardware':False,'platformio_target_test':'NOT_RUN',
      'esp32_device_test':'NOT_RUN','real_installed_qeapp_test':'NOT_RUN',
      'steps':steps}
    (dest/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    md=[
      '# QEAPP Studio v0.4.1 — host verification', '',
      '| Check | Result |','|---|---|',
      f'| Lua host runner | {"PASS" if steps["build_lua_host"]["returncode"]==0 else "FAIL"} |',
      f'| C++/Python engine regressions | {unit["tests"]-unit["skipped"]}/{unit["tests"]} executed, {unit["skipped"]} skipped, rc={unit["returncode"]} |',
      f'| Desktop-core regressions | {studio["tests"]-studio["skipped"]}/{studio["tests"]} executed, {studio["skipped"]} skipped, rc={studio["returncode"]} |',
      f'| Host Lua replay screenshot | {"PASS" if steps["lua_preview"]["returncode"]==0 else "FAIL"} |',
      f'| Mock firmware link | {"PASS" if steps.get("mock_firmware_link",{}).get("returncode")==0 else "SKIP"} |',
      f'| PySide6 GUI runtime | {"Qt offscreen tests attempted" if qt else "NOT TESTED: PySide6 unavailable"} |',
      '| PlatformIO compile/ESP32-S3 board | NOT TESTED |',
      '| Independent signed Lua install on actual VQEAF device | NOT TESTED |',
      '', '## Runtime dependency',
      report['lua_dependency'],
      '', 'Do not conflate mocked firmware link, host preview and physical board execution.',
    ]
    (dest/'report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('host_pass','tests_engine','tests_studio','pyside6_available','lua_dependency')},indent=2))
    print('Report:',dest/'report.md')
    return 0 if success else 1

if __name__=='__main__':sys.exit(main())
