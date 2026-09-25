#!/usr/bin/env python3
"""Headless interactive virtual-phone smoke: actual Lua VM + RGB565 stream.

This PC-only probe is NOT an ESP32, MRE, or Symbian emulator. It exercises
exactly the same local host process used by the PySide6 virtual phone.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from studio.core.frame_protocol import FrameDecoder, PIXEL_BYTES, rgb565_to_rgb888, WIDTH, HEIGHT
from studio.core.host_metrics import parse_metric
from tools.simulate_host import png_bytes

class VirtualTestError(ValueError): pass

def capture(source: Path, outfile: Path, frames: int = 8, press: str = 'start',
            exe: Path|None=None) -> dict:
    from studio.core.replays import VALID_KEYS
    if press not in VALID_KEYS: raise VirtualTestError('Reserved or unknown host key')
    if not 1<=frames<=100:raise VirtualTestError('1..100 frames required')
    source=source.resolve(strict=True)
    if source.is_symlink() or source.suffix!='.lua' or not 0<source.stat().st_size<=65536:
        raise VirtualTestError('Invalid Lua source')
    exe=exe or ROOT/'build'/('qe_lua_host.exe' if sys.platform=='win32' else 'qe_lua_host')
    if not exe.is_file():raise VirtualTestError('Run tools/build_lua_host.py first')
    process=subprocess.Popen([str(exe),str(source),'--interactive'],stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert process.stdin and process.stdout and process.stderr
    dec=FrameDecoder()
    last=None
    started=time.monotonic()
    try:
        process.stdin.write(f'KEY {press} 1\n'.encode('ascii'))
        process.stdin.write(f'KEY {press} 0\n'.encode('ascii'))
        for i in range(frames):
            process.stdin.write(b'TICK 67\n')
        process.stdin.flush()
        for i in range(frames):
            # Every TICK creates one 129600-byte frame. Header stays bounded;
            # exact length avoids waiting for next frame or consuming stderr.
            header=process.stdout.readline(40)
            if header!=f'QEFRAME {i}\n'.encode():
                raise VirtualTestError('Unexpected frame header or guest failure')
            raw=process.stdout.read(PIXEL_BYTES)
            if len(raw)!=PIXEL_BYTES:raise VirtualTestError('Truncated VM framebuffer')
            parsed=dec.feed(header+raw)
            if len(parsed)!=1:raise VirtualTestError('Frame decoder mismatch')
            last=parsed[0]
        process.stdin.write(b'QUIT\n')
        process.stdin.flush()
        process.stdin.close()
        if process.wait(timeout=12):
            raise VirtualTestError('Guest failed: '+process.stderr.read().decode('utf8','replace')[-1500:])
        stderr = process.stderr.read().decode('utf-8','replace')
        metrics = [m for line in stderr.splitlines() if (m := parse_metric(line))]
        assert last is not None
        # Compose 29/21 OS shell bars; guest draws the middle 270 lines.
        body=rgb565_to_rgb888(last.rgb565_le)
        rgb=bytes((24,60,32))*(29*WIDTH)+body+bytes((24,60,32))*(21*WIDTH)
        outfile.parent.mkdir(parents=True,exist_ok=True)
        outfile.write_bytes(png_bytes(240,320,rgb))
        elapsed=max(.0001,time.monotonic()-started)
        return {'mode':'REAL_PC_LUA_VM_NOT_ESP32','frames':frames,'frame_bytes':PIXEL_BYTES,
                'host_throughput_fps':round(frames/elapsed,2),
                'host_metric':(metrics[-1].__dict__ if metrics else None),
                'image':str(outfile),'hardware_tested':False,'protocol':'QEFRAME/1'}
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        if process.stdin and not process.stdin.closed: process.stdin.close()
        if process.stdout and not process.stdout.closed: process.stdout.close()
        if process.stderr and not process.stderr.closed: process.stderr.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('lua_source',type=Path)
    p.add_argument('-o','--output',type=Path,required=True)
    p.add_argument('--frames',type=int,default=8)
    p.add_argument('--press',default='start')
    args=p.parse_args()
    try:
        print(json.dumps(capture(args.lua_source,args.output,args.frames,args.press),indent=2))
        return 0
    except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
        print('VIRTUAL_PHONE_FAIL:',exc,file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())
