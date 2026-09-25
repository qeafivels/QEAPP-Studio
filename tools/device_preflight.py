#!/usr/bin/env python3
"""Non-mutating Lua beta ESP32-S3 preflight. Never claims a mock/host as device proof."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from studio_firmware import firmware_root
import shutil

ROOT=Path(__file__).resolve().parents[1]


def inspect(fw: Path, cli: str | None = None, source_root: Path = ROOT) -> dict:
    fw=fw.resolve(strict=True)
    checks={}
    def check(name: str, ok: bool, detail: str, remedy: str = ''):
        checks[name]={'status':'READY' if ok else 'MISSING', 'detail':detail}
        if remedy and not ok:checks[name]['action']=remedy

    ini=fw/'platformio.ini'
    pio=ini.read_text(encoding='utf-8') if ini.is_file() else ''
    beta=pio.split('[env:vqeaf_lua_beta]',1)[1].split('[env:',1)[0] if '[env:vqeaf_lua_beta]' in pio else ''
    standard=pio.split('[env:vqeaf_os]',1)[1].split('[env:',1)[0] if '[env:vqeaf_os]' in pio else ''
    check('beta_profile',all(x in beta for x in ('VQEAF_ENABLE_LUA=1','QE_LUA_PSRAM_ALLOC=1','VQEAF_LUA_BETA_TRUST=1')),
          'Explicit Lua beta enable, PSRAM allocator, separate signature root',
          'Update platformio.ini from the Studio firmware patch')
    check('stock_isolated','VQEAF_ENABLE_LUA=1' not in standard,
          'Default production firmware does not expose Lua beta', 'Remove beta flags from stock env')
    vendor=fw/'lib/VqeafLua54/src'
    check('lua_source',all((vendor/p).is_file() for p in ('lua.h','lua.c','lauxlib.c','lualib.h')),
          'Bundled official Lua 5.4 source is required for real device linking',
          'python tools/bootstrap_lua.py (inspect SHA-256 before installation)')
    key=fw/'src/services/QeappTrustKeyLuaBeta.h'
    key_text=key.read_text(encoding='utf-8') if key.is_file() else ''
    check('beta_public_key','Lua beta publisher not configured' not in key_text and 'BEGIN PRIVATE KEY' not in key_text and bool(key_text.strip()),
          'Beta public key is provisioned, never a private key',
          'python tools/provision_lua_beta_key.py --private PATH_OUTSIDE_REPO')
    host=source_root/'runtime/src/QeLuaRuntime.cpp'
    target=fw/'src/lua/QeLuaRuntime.cpp'
    shared=host.read_text() if host.is_file() else ''
    mirror=target.read_text() if target.is_file() else ''
    check('runtime_mirror',bool(shared and mirror=='#if defined(VQEAF_ENABLE_LUA) && VQEAF_ENABLE_LUA\n'+shared+'\n#endif // VQEAF_ENABLE_LUA\n'),
          'Firmware VM must match desktop VM implementation exactly',
          'Copy runtime/include/QeLuaRuntime.h and mirrored .cpp to firmware src/lua/')
    check('platformio',bool(cli or shutil.which('pio')),
          'PlatformIO is available on PATH', 'Install PlatformIO CLI and select env vqeaf_lua_beta')
    ready=all(v['status']=='READY' for v in checks.values())
    return {'status':'READY_FOR_DEVICE_BUILD' if ready else 'NOT_READY',
            'target':'ESP32-S3-WROOM-1 N16R8','profile':'vqeaf_lua_beta',
            'device_build':'NOT_RUN','hardware_test':'NOT_RUN',
            'checks':checks}


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--firmware-root',type=Path,default=firmware_root())
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    try:
        if args.firmware_root is None: ap.error('Clone VQEAF-OS next to Studio or set QEAPP_FIRMWARE_ROOT')
        report=inspect(args.firmware_root)
    except (OSError,ValueError) as exc:
        ap.exit(2,'PREFLIGHT_FAIL: '+str(exc)+'\n')
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding='utf-8')
    print(text,end='')
    return 0 if report['status']=='READY_FOR_DEVICE_BUILD' else 3

if __name__=='__main__':raise SystemExit(main())
