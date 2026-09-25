#!/usr/bin/env python3
"""Convert a tiny PNG mask into inlined, bounded `engine.blit1` Lua source.

Asset conversion is a developer-host tool, not part of the ESP32 firmware.
Nothing is loaded from disk at runtime; the binary mask sits in signed main.lua.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

class SpriteError(ValueError):
    pass


def pack_mask(image, mode: str = 'alpha', threshold: int = 128) -> tuple[int,int,bytes]:
    if mode not in ('alpha', 'dark', 'light'):
        raise SpriteError('Mask mode must be alpha, dark or light')
    if type(threshold) is not int or not 0 <= threshold <= 255:
        raise SpriteError('Threshold must be an integer in 0..255')
    w,h = image.size
    if not (1 <= w <= 32 and 1 <= h <= 32):
        raise SpriteError('blit1 sprite dimensions must each be 1..32 pixels; never auto-resize')
    rgba=image.convert('RGBA')
    data=bytearray((w*h+7)//8)
    pixels=rgba.load()
    for n in range(w*h):
        red,green,blue,alpha=pixels[n%w,n//w]
        if mode=='alpha':
            enabled=alpha > 0 and alpha >= threshold
        else:
            # Standard fixed integer luminance approximation; alpha always gates.
            lum=(299*red+587*green+114*blue+500)//1000
            enabled=alpha > 0 and alpha >= threshold and (lum<threshold if mode=='dark' else lum>=threshold)
        if enabled:data[n//8] |= 0x80>>(n%8)
    return w,h,bytes(data)


def lua_snippet(png: Path, symbol: str = 'sprite', mode: str = 'alpha', threshold: int = 128,
                color: int = 0xFFFF) -> str:
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,39}', symbol):
        raise SpriteError('Symbol must be 1..40 ASCII Lua identifier characters')
    if type(color) is not int or not 0 <= color <= 65535:
        raise SpriteError('RGB565 color must be 0..65535')
    if png.suffix.lower() != '.png' or png.is_symlink() or not png.is_file():
        raise SpriteError('Select a regular PNG file (not a symlink)')
    if png.stat().st_size>1024*1024:
        raise SpriteError('PNG input too large (limit: 1 MiB)')
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise SpriteError('Pillow is required: pip install Pillow') from exc
    # Decompression bomb check before decoding even though mask max is 32x32.
    with Image.open(png) as source:
        if source.format!='PNG':raise SpriteError('Input must be a PNG')
        w,h,bits=pack_mask(source, mode, threshold)
    escaped=''.join(f'\\x{x:02X}' for x in bits)
    return (f'-- {symbol}: {w}x{h} 1-bit sprite; row-major MSB-first; transparent zeros.\n'
            f'local {symbol}_bits = "{escaped}"\n'
            f'local {symbol}_w, {symbol}_h = {w}, {h}\n'
            f'-- Draw inside on_draw():\n'
            f'-- engine.blit1(20, 20, {symbol}_w, {symbol}_h, {symbol}_bits, 0x{color:04X})\n')


def main() -> int:
    p=argparse.ArgumentParser(description='PNG -> Lua engine.blit1 asset (1-bit, 32x32 max)')
    p.add_argument('input', type=Path)
    p.add_argument('--name', default='sprite')
    p.add_argument('--mode', choices=['alpha','dark','light'], default='alpha')
    p.add_argument('--threshold',type=int,default=128)
    p.add_argument('--color',type=lambda s:int(s,0),default=0xFFFF)
    p.add_argument('-o','--output',type=Path)
    a=p.parse_args()
    try:snippet=lua_snippet(a.input,a.name,a.mode,a.threshold,a.color)
    except (SpriteError, OSError, ValueError) as exc:
        p.exit(2,'SPRITE_ERROR: '+str(exc)+'\n')
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(snippet,encoding='utf-8')
        print('Wrote:',a.output)
    else:print(snippet,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
