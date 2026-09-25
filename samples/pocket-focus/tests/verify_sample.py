#!/usr/bin/env python3
"""Pocket Focus host verification; NEVER claims real ESP32 GUI or device installation."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Monorepo checkout: firmware is at the VQEAF-OS repository root, not a duplicated copy.
# For a standalone Studio checkout, allow QEAPP_FIRMWARE_ROOT to point to firmware.
def firmware_root(studio:Path):
    override=os.environ.get('QEAPP_FIRMWARE_ROOT')
    if override:return Path(override).expanduser().resolve()
    candidate=studio.parent.parent
    if (candidate/'tools/build_qeapp.py').is_file():return candidate
    legacy=studio/'firmware/VQEAF-OS'
    if legacy.is_dir():return legacy
    raise RuntimeError('VQEAF OS firmware source missing; set QEAPP_FIRMWARE_ROOT')
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'projects/pocket-focus-lua'
GUIDE=ROOT/'projects/pocket-focus-guide'
PREVIEWS=('home','running','paused','settings','stats','end_dialog','resume')

def invoke(cmd, env=None):
    proc=subprocess.run(cmd,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=120,env=env)
    if proc.returncode:
        raise RuntimeError(f'Command failed ({proc.returncode}): {" ".join(map(str,cmd))}\n{proc.stderr[-1800:]}')
    return proc.stdout.strip()

def verify(studio:Path, system_lua:bool=False):
    studio=studio.resolve(strict=True)
    q=studio/'tools/qstudio.py'; prev=studio/'tools/lua_preview.py'
    if not q.exists() or not prev.exists():raise RuntimeError('Expected QEAPP Studio 0.7.4 source root')
    result={'mode':'PC HOST ONLY','hardware':'NOT_TESTED','gui':'NOT_TESTED','checks':[],'images':[]}
    for target in (APP,GUIDE):
        invoke([sys.executable,str(q),'validate',str(target)])
        result['checks'].append('VALID project '+target.name)
    env=os.environ.copy()
    if system_lua:env['QEAPP_HOST_SYSTEM_LUA']='1'
    if not (studio/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')).exists():
        invoke([sys.executable,str(studio/'tools/build_lua_host.py')]+(['--system-lua'] if system_lua else []))
    for name in PREVIEWS:
        img=ROOT/'screenshots'/(name+'.png')
        output=invoke([sys.executable,str(prev),str(APP/'main.lua'),'--frames','30','--replay',str(APP/'tests'/(name+'.json')),'-o',str(img)],env=env)
        value=json.loads(output)
        assert value['status']=='LUA_HOST_PASS' and value['replayed_input_events']>0
        assert img.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
        result['checks'].append('REAL HOST LUA '+name)
        result['images'].append({'name':name,'sha256':hashlib.sha256(img.read_bytes()).hexdigest()})
    # Short-duration TEST-ONLY source: 0.6s work, 30s break. Nothing is changed in the shipped app.
    with tempfile.TemporaryDirectory(prefix='pocketfocus-') as tmp:
        t=Path(tmp)
        script=(APP/'main.lua').read_text(encoding='utf-8')
        assert 'local W_PRESETS = {15,25,45}' in script and 'local B_PRESETS = {3,5,10}' in script
        script=script.replace('local W_PRESETS = {15,25,45}','local W_PRESETS = {0.01,0.01,0.01}')
        script=script.replace('local B_PRESETS = {3,5,10}','local B_PRESETS = {0.5,0.5,0.5}')
        fast=t/'fast.lua'; fast.write_text(script,encoding='utf-8')
        # Capture frame with short test fixture. Must have green break border.
        fast_png=t/'break.png'
        invoke([sys.executable,str(prev),str(fast),'--frames','30','--replay',str(APP/'tests/running.json'),'-o',str(fast_png)],env=env)
        from PIL import Image
        with Image.open(fast_png) as im:
            color=im.convert('RGB').getpixel((13,94))
            assert color[1]>color[0]*1.7, f'Expected green break border, got {color}'
        result['checks'].append('WORK -> BREAK timed phase transition')
        fast.write_text(script.replace('local autoBreak=true','local autoBreak=false'),encoding='utf-8')
        done_png=t/'done.png'
        invoke([sys.executable,str(prev),str(fast),'--frames','30','--replay',str(APP/'tests/running.json'),'-o',str(done_png)],env=env)
        with Image.open(done_png) as im:
            color=im.convert('RGB').getpixel((12,99))
            assert color[1]>color[0]*1.7, f'Expected completion green border, got {color}'
        result['checks'].append('AUTO BREAK OFF -> completion')
        # E2E signing uses ephemeral key, NEVER include in artifacts or treat as real device trust.
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        k=ec.generate_private_key(ec.SECP256R1())
        private=t/'ephemeral-private.pem'; public=t/'ephemeral-public.pem'
        private.write_bytes(k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        public.write_bytes(k.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
        for label,proj,fw,keyid,opts in (
            ('guide',GUIDE,firmware_root(studio),'0x31534351',[]),
            ('lua-beta',APP,firmware_root(studio),'0x544c5541',['--experimental-lua'])):
            package=t/(label+'.qeapp')
            invoke([sys.executable,str(q),'build',str(proj),'--firmware-root',str(fw),'--sign-key',str(private),'--key-id',keyid,'-o',str(package),*opts])
            inspect=json.loads(invoke([sys.executable,str(q),'inspect',str(package),'--public-key',str(public),'--key-id',keyid]))
            assert inspect['section_sha256']=='PASS' and inspect['signature'].startswith('PASS')
            result['checks'].append(label+' host signed package + verify supplied temporary public key')
    reports=ROOT/'reports';reports.mkdir(exist_ok=True)
    (reports/'host_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checks':len(result['checks']),'result':'HOST PASS','device':'NOT_TESTED'},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--studio',type=Path,required=True);p.add_argument('--system-lua',action='store_true');args=p.parse_args()
    try:verify(args.studio,args.system_lua)
    except (RuntimeError,OSError,AssertionError,subprocess.TimeoutExpired) as err:
        print('SAMPLE TEST FAIL:',err,file=sys.stderr);sys.exit(1)
