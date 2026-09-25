#!/usr/bin/env python3
"""Build/test portable C++ Lua VM on PC; export a 240x320 preview PNG.
Do not mistake this framebuffer preview for ESP32-S3 hardware verification.
"""
from __future__ import annotations
import argparse
import re
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# The CLI can be launched directly as a file, and imported by unittest.
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from tools.simulate_host import png_bytes
from studio.core.replays import parse as parse_replay, as_host_lines, MAX_REPLAY_BYTES

def convert_ppm(data: bytes) -> bytes:
    parts=data.split(b'\n',3)
    if len(parts)!=4 or parts[:3]!=[b'P6',b'240 270',b'255'] or len(parts[3])!=240*270*3:
        raise ValueError('Unexpected Lua host PPM size/header')
    rgb=parts[3]
    # Firmware compositor reserves 29 status rows + 21 footer rows; screenshot
    # is deliberately framed as a host mock, not actual ST7789 output.
    header=b'\x18\x3c\x20'*(240*29)
    footer=b'\x18\x3c\x20'*(240*21)
    return png_bytes(240,320,header+rgb+footer)

def prepare_replay(replay: Path, dest: Path, frames: int) -> int:
    replay = replay.resolve(strict=True)
    if replay.stat().st_size > MAX_REPLAY_BYTES:
        raise ValueError('Replay too large (max 8192 bytes)')
    events = parse_replay(replay.read_bytes(), frames)
    dest.write_text(as_host_lines(events, frames), encoding='ascii')
    return len(events)

def preview(source: Path, target: Path,frames: int,replay: Path|None=None) -> dict:
    source=source.resolve(strict=True)
    if source.suffix!='.lua' or source.is_symlink() or not 0<source.stat().st_size<=64*1024:
        raise ValueError('Lua source must be a regular .lua file <=64 KiB')
    if frames<1 or frames>200:raise ValueError('Frames must be 1..200')
    exe=ROOT/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')
    if not exe.is_file():
        cmd=[sys.executable,str(ROOT/'tools/build_lua_host.py')]
        if os.environ.get('QEAPP_HOST_SYSTEM_LUA')=='1':cmd+=['--system-lua']
        subprocess.run(cmd,cwd=ROOT,check=True,timeout=160)
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qeapp-lua-') as temp:
        ppm=Path(temp)/'frame.ppm'
        cmd=[str(exe),str(source),str(ppm),str(frames),'192']
        event_count=0
        if replay is not None:
            spec=Path(temp)/'events.txt'
            event_count=prepare_replay(replay,spec,frames)
            cmd.append(str(spec))
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        if result.returncode:raise RuntimeError('Lua host FAILED: '+result.stderr.strip())
        data=convert_ppm(ppm.read_bytes())
    target.write_bytes(data)
    return {'status':'LUA_HOST_PASS', 'frames':frames, 'image':str(target),
            'runtime_log':result.stdout.strip(), 'replayed_input_events':event_count, 'target_hardware':'NOT_TESTED',
            'device_firmware_build':'NOT_VERIFIED'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path)
    ap.add_argument('-o','--output',type=Path,required=True)
    ap.add_argument('--frames',type=int,default=8)
    ap.add_argument('--replay',type=Path,help='JSON input replay (max 128 app-only events)')
    args=ap.parse_args()
    try:print(json.dumps(preview(args.source,args.output,args.frames,args.replay),indent=2));return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as err:
        print('LUA_PREVIEW_FAIL: '+str(err),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
