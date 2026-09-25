#!/usr/bin/env python3
"""Set up a DEDICATED beta P-256 signing key outside Git; production key unchanged.
Generated beta PUBLIC header is compiled only by vqeaf_lua_beta.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
from studio_firmware import firmware_root
ROOT=Path(__file__).resolve().parents[1]
FW=firmware_root()
KEY_ID=0x544c5541
PLACEHOLDER='Lua beta publisher not configured'
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--private',type=Path,required=True,help='A NEW path OUTSIDE QEAPP Studio/repository')
 ap.add_argument('--firmware-root',type=Path,default=FW)
 args=ap.parse_args()
 if args.firmware_root is None: ap.error('Clone VQEAF-OS next to Studio or set QEAPP_FIRMWARE_ROOT')
 fw=args.firmware_root.resolve(strict=True)
 priv=args.private.expanduser().resolve()
 if priv.exists():raise ValueError('Key exists: refusing to overwrite')
 for root in (ROOT.resolve(),fw):
  if priv==root or root in priv.parents:raise ValueError('Private key MUST be outside repository')
 header=fw/'src/services/QeappTrustKeyLuaBeta.h'
 if header.exists() and PLACEHOLDER not in header.read_text():
  raise ValueError('Existing beta public header: reusing existing publisher is required')
 subprocess.run([sys.executable,str(fw/'tools/qeapp_keys.py'),
       '--private',str(priv),'--header',str(header),'--key-id',hex(KEY_ID)],check=True)
 print('Studio build key_id:',hex(KEY_ID))
 print('Back up private PEM safely; DO NOT commit, copy to SD, or share it.')
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (ValueError,OSError,subprocess.CalledProcessError) as exc:
  raise SystemExit('PROVISION FAILED: '+str(exc))
