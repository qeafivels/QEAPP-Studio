#!/usr/bin/env python3
"""Read-only diagnosis by default; --apply repairs corrupt user settings only."""
import argparse
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studio.core import repair

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true',help='Back up and reset invalid settings.json only')
    p.add_argument('--json',action='store_true')
    a=p.parse_args()
    checks=repair.inspect()
    if a.json:print(repair.as_json(checks))
    else:
        for c in checks:print(f'[{c.status}] {c.name}: {c.detail}')
    if a.apply:
        backup=repair.apply()
        print('BACKUP:', str(backup) if backup else 'No corrupt settings; nothing changed')
    return 2 if any(c.status=='FAIL' for c in checks) else 0

if __name__=='__main__':raise SystemExit(main())
