#!/usr/bin/env python3
"""Find the separate VQEAF-OS checkout. Never vendor firmware into Studio."""
from __future__ import annotations
import os
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parents[1]

def firmware_root(*, required: bool = False) -> Path | None:
    configured = os.environ.get('QEAPP_FIRMWARE_ROOT')
    if configured:
        p=Path(os.path.expandvars(configured)).expanduser().resolve()
        if (p/'platformio.ini').is_file():return p
        if required:raise FileNotFoundError(f'QEAPP_FIRMWARE_ROOT is not a firmware checkout: {p}')
        return None
    for candidate in (STUDIO_ROOT.parent/'VQEAF-OS', STUDIO_ROOT/'firmware/VQEAF-OS'):
        if (candidate/'platformio.ini').is_file():return candidate.resolve()
    if required:raise FileNotFoundError('Clone VQEAF-OS next to QEAPP-Studio or set QEAPP_FIRMWARE_ROOT')
    return None

if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--require',action='store_true')
    args=ap.parse_args()
    try:print(firmware_root(required=args.require) or 'Firmware not installed (host IDE can still run)')
    except FileNotFoundError as exc:ap.exit(2,f'ERROR: {exc}\n')
