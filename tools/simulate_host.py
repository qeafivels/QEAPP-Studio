#!/usr/bin/env python3
"""Compile and run M1 native host Snake proof-of-concept, export a PNG.

HOST ONLY: never produces QEAPP packages. Requires C++17 g++ or clang++.
No third-party Python dependencies and no flashing/hardware implied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['engine/src/runtime.cpp','engine/src/draw.cpp','engine/host/HostCanvas.cpp']
DEMO_SOURCES = {
    'snake':['examples/snake_native_host/SnakeDemo.cpp','examples/snake_native_host/main.cpp'],
    'hello':['examples/hello_native_host/main.cpp']
}
INCLUDES = ['engine/include','engine/host','examples/snake_native_host']

class SimulatorError(Exception): pass

def compile_host(output: Path, compiler: str | None = None, demo: str = 'snake') -> None:
    if demo not in DEMO_SOURCES:
        raise SimulatorError('Unsupported native host demo')
    cc = compiler or shutil.which('g++') or shutil.which('clang++')
    if not cc:
        raise SimulatorError('C++17 g++/clang++ compiler unavailable')
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [cc,'-std=c++17','-O2','-Wall','-Wextra','-Werror','-pedantic',
           *[arg for folder in INCLUDES for arg in ('-I',str(ROOT/folder))],
           *[str(ROOT/src) for src in SOURCES+DEMO_SOURCES[demo]],'-o',str(output)]
    result = subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    if result.returncode:
        raise SimulatorError('Host compilation failed:\n'+result.stderr[-8000:])

def parse_ppm(ppm: bytes) -> tuple[int,int,bytes]:
    # Internal trusted, deterministic PPM writer: precisely three newline headers.
    parts = ppm.split(b'\n',3)
    if len(parts)!=4 or parts[0]!=b'P6' or parts[2]!=b'255':
        raise SimulatorError('Invalid PPM header')
    try:
        width,height = (int(x) for x in parts[1].split())
    except ValueError as err:
        raise SimulatorError('Invalid PPM dimensions') from err
    if width!=240 or height!=320 or len(parts[3])!=width*height*3:
        raise SimulatorError('Unexpected framebuffer size')
    return width,height,parts[3]

def png_bytes(width: int, height: int, rgb: bytes) -> bytes:
    if width!=240 or height!=320 or len(rgb)!=width*height*3:
        raise SimulatorError('Invalid RGB888 frame')
    row_bytes=width*3
    rows=b''.join(b'\x00'+rgb[y*row_bytes:(y+1)*row_bytes] for y in range(height))
    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'
        +chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))
        +chunk(b'IDAT',zlib.compress(rows,level=9))
        +chunk(b'IEND',b''))

def simulate(out: Path, scenario: str='playing', frames: int=40,
             compiler: str | None = None, demo: str = 'snake') -> dict:
    if demo not in DEMO_SOURCES or scenario not in ('playing','ready','paused') or not 0<=frames<=2000:
        raise SimulatorError('Invalid scenario/frames')
    out=out.resolve()
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='qeapp-host-') as work:
        work=Path(work)
        exe=work/'snake_host'
        ppm=work/'image.ppm'
        compile_host(exe,compiler,demo)
        run=subprocess.run([str(exe),'--out',str(ppm),'--scenario',scenario,
            '--frames',str(frames)],capture_output=True,text=True,timeout=30)
        if run.returncode:
            raise SimulatorError('Host run failed: '+run.stderr.strip())
        w,h,rgb=parse_ppm(ppm.read_bytes())
    output=png_bytes(w,h,rgb)
    out.write_bytes(output)
    return {'status':'HOST_ONLY_PASS','demo':demo,'scenario':scenario,'frames':frames,
            'width':w,'height':h,'png_sha256':hashlib.sha256(output).hexdigest(),
            'rgb_sha256':hashlib.sha256(rgb).hexdigest(),'output':str(out),
            'runtime_log':run.stdout.strip(),
            'qeapp_game_package':'NOT_SUPPORTED','esp32_firmware':'NOT_TESTED'}

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--demo',choices=['snake','hello'],default='snake')
    ap.add_argument('--scenario',choices=['ready','playing','paused'],default='playing')
    ap.add_argument('--frames',type=int,default=40)
    ap.add_argument('--compiler')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    try:
        report=simulate(args.out,args.scenario,args.frames,args.compiler,args.demo)
        print(json.dumps(report,indent=2))
        return 0
    except (SimulatorError,OSError,subprocess.TimeoutExpired) as err:
        print(f'HOST_SIM_FAILED: {err}',file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())
