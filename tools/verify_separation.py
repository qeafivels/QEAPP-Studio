#!/usr/bin/env python3
"""Bytewise standalone file checks and optional GitHub tree validation.

No private tokens handled; GitHub CLI manages authentication.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'STANDALONE_FILES_SHA256.json'
REPO = 'qeafivels/QEAPP-Studio'

def sha1_blob(content: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify-remote',action='store_true',help='Verify published new GitHub repo file-by-file before OS cleanup')
    args=ap.parse_args()
    data=json.loads(MANIFEST.read_text(encoding='utf-8'))
    paths=data['files']
    if len(paths)<220:raise SystemExit('ERROR: unexpectedly small manifest')
    bad=[]
    for filename,digest in sorted(paths.items()):
        p=ROOT / filename
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:bad.append(filename)
    if bad:
        print('MISSING OR CHANGED:',*bad,sep='\n- ')
        return 1
    print(f'LOCAL PASS: {len(paths)} files agree with SHA-256 manifest')
    if args.verify_remote:
        try:
            run=subprocess.run(['gh','api',f'repos/{REPO}/git/trees/main?recursive=1'],check=True,
                           capture_output=True,text=True,timeout=60)
            raw=json.loads(run.stdout)
        except (OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired,json.JSONDecodeError) as e:
            print('Cannot verify remote GitHub repository (is it created and pushed?):',str(e)[:200]);return 2
        if raw.get('truncated'):print('ERROR: GitHub tree is truncated; cannot trust this result');return 2
        remote={x['path']:x['sha'] for x in raw.get('tree',[]) if x['type']=='blob'}
        unmatched=[p for p in paths if remote.get(p)!=sha1_blob((ROOT/p).read_bytes())]
        if unmatched:
            print(f'GITHUB MISMATCH: {len(unmatched)} files',*unmatched[:8],sep='\n- ')
            return 3
        print(f'GITHUB PASS: all {len(paths)} local files match {REPO}/main Git blobs')
    return 0

if __name__=='__main__':raise SystemExit(main())
