#!/usr/bin/env python3
"""Fetch official Lua 5.4.8 source once (on developer machine), verify SHA256,
install a reproducible, licensed PlatformIO library. No network at device runtime.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import shutil
import tarfile
import urllib.request
from pathlib import Path
from studio_firmware import firmware_root

URL = 'https://www.lua.org/ftp/lua-5.4.8.tar.gz'
SHA256 = '4f18ddae154e793e46eeab727c59ef1c0c0c2b744e7b94219710d76f530629ae'
CORE = {
    'lapi.c','lcode.c','lctype.c','ldebug.c','ldo.c','ldump.c','lfunc.c',
    'lgc.c','llex.c','lmem.c','lobject.c','lopcodes.c','lparser.c',
    'lstate.c','lstring.c','ltable.c','ltm.c','lundump.c','lvm.c','lzio.c',
    'lauxlib.c','lbaselib.c','lmathlib.c','lstrlib.c','ltablib.c','lutf8lib.c',
}  # omit io/os/package/dynamic-loader/debug libs, Lua CLI/bytecode tool

def install(firmware: Path, archive: Path | None = None) -> int:
    firmware = firmware.resolve()
    if not (firmware/'platformio.ini').exists():
        raise ValueError('Not a VQEAF-OS firmware root')
    payload = archive.read_bytes() if archive else urllib.request.urlopen(URL,timeout=40).read(512*1024)
    if hashlib.sha256(payload).hexdigest() != SHA256:
        raise ValueError('Lua 5.4.8 SHA256 mismatch: installation cancelled')
    dest=firmware/'lib'/'VqeafLua54'/'src'
    dest.mkdir(parents=True,exist_ok=True)
    copied=[]
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as tf:
        for member in tf:
            if not member.isfile() or not member.name.startswith('lua-5.4.8/src/'):
                continue
            base=Path(member.name).name
            if not (base.endswith('.h') or base in CORE):
                continue
            if member.size>512*1024:
                raise ValueError('Unexpected Lua source size')
            fp=tf.extractfile(member)
            if fp is None:raise ValueError('Missing archive file')
            (dest/base).write_bytes(fp.read())
            copied.append(base)
    (dest.parent/'UPSTREAM.txt').write_text('Lua 5.4.8 original source: '+URL+'\nSHA256: '+SHA256+'\nLicense: MIT (see LICENSE in upstream archive)\n',encoding='utf-8')
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:gz') as tf:
        license_item=next((m for m in tf if m.isfile() and m.name in ('lua-5.4.8/COPYRIGHT','lua-5.4.8/LICENSE')),None)
        if license_item:
            license_source=tf.extractfile(license_item)
            if license_source:(dest.parent/'LICENSE.lua').write_bytes(license_source.read())
    if not CORE.issubset(copied) or not {'lua.h','lauxlib.h','lualib.h'}.issubset(copied):
        raise ValueError('Missing Lua compiler source modules')
    (dest.parent/'library.json').write_text('{"name":"VqeafLua54","version":"5.4.8","build":{"includeDir":"src"},"frameworks":"*","platforms":"*"}\n')
    print(f'Installed {len(copied)} verified Lua 5.4.8 upstream files into {dest}.')
    return 0
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--firmware-root',type=Path,default=firmware_root())
    p.add_argument('--archive',type=Path,help='Offline official lua-5.4.8.tar.gz (same SHA256)')
    args=p.parse_args()
    try:
        if args.firmware_root is None: p.error('Clone VQEAF-OS next to Studio or set QEAPP_FIRMWARE_ROOT')
        raise SystemExit(install(args.firmware_root,args.archive))
    except (OSError,ValueError) as exc:raise SystemExit('ERROR: '+str(exc))
