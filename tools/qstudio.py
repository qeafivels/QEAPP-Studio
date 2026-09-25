#!/usr/bin/env python3
"""QEAPP Studio: web/text QEAPP/2, opt-in experimental signed Lua QEAPP/2.

Lua package requires vqeaf_lua_beta firmware and uses the original firmware signer.
No private key is copied or logged. Host signature verification is opt-in via
--public-key and does not replace verification against the device trust anchor.
"""
from __future__ import annotations
import argparse
import os
import shutil
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

MAGIC = b'QEAPP2\r\n'
TRAILER_MAGIC = b'QSIGP256'
MAX_TEXT = 262144
SCHEMA_KEYS = {'project_format','id','name','version','type','content','url','icon'}

class ProjectError(ValueError):
    pass

def within_project(project: Path, rel: str) -> Path:
    if not isinstance(rel, str) or not rel or '\\' in rel or Path(rel).is_absolute():
        raise ProjectError('Asset path must be a relative POSIX path')
    pp=Path(rel)
    if any(p in ('.','..') for p in pp.parts):
        raise ProjectError('Asset path traversal is forbidden')
    root=project.resolve(strict=True)
    cursor=root
    for part in pp.parts:
        cursor=cursor/part
        if cursor.is_symlink():raise ProjectError('Symlinks are not accepted as package inputs')
    target=cursor.resolve(strict=True)
    try:
        target.relative_to(root)
    except ValueError as err:
        raise ProjectError('Asset must remain within project; no symlink escape') from err
    if not target.is_file():
        raise ProjectError('Asset must be a regular file')
    return target

def validate(project: Path) -> tuple[dict, dict[str, Path]]:
    project=project.resolve(strict=True)
    cfg=project/'qeapp.project.json'
    if not cfg.is_file() or cfg.is_symlink():
        raise ProjectError('Missing regular qeapp.project.json')
    try:
        obj=json.loads(cfg.read_text(encoding='utf-8'))
    except (ValueError,UnicodeError) as err:
        raise ProjectError('Invalid UTF-8 project JSON') from err
    if not isinstance(obj,dict):
        raise ProjectError('Project JSON must be an object')
    if obj.get('type')=='lua-proposal':
        raise ProjectError('NOT_IMPLEMENTED legacy lua-proposal: use explicit type=lua with experimental vqeaf_lua_beta firmware')
    if obj.get('project_format') != 1:
        raise ProjectError('Unsupported project_format; expected 1')
    unknown=set(obj)-SCHEMA_KEYS
    if unknown:
        raise ProjectError('Unknown metadata keys: '+','.join(sorted(unknown)))
    appid=obj.get('id')
    if not isinstance(appid,str) or not re.fullmatch(r'[a-z0-9_-]{1,24}',appid):
        raise ProjectError('Invalid app ID')
    name=obj.get('name')
    if not isinstance(name,str) or not (1<=len(name)<=40) or not name.isascii() or any(ord(c)<32 or ord(c)>126 for c in name):
        raise ProjectError('Name must be 1..40 printable ASCII bytes')
    version=obj.get('version')
    if not isinstance(version,str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*', version) or len(version)>19:
        raise ProjectError('Version must be numeric dotted, <=19 characters')
    kind=obj.get('type')
    if kind not in ('web','text','lua'):
        raise ProjectError('Unsupported project type (web/text/lua)')
    assets={}
    if kind=='web':
        if set(obj)&{'content'} or not isinstance(obj.get('url'),str):
            raise ProjectError('Web apps require url and forbid content')
        url=obj['url']
        u=urlsplit(url)
        if (u.scheme!='https' or not u.hostname or u.username or u.password or
            len(url.encode('utf-8'))>192 or not url.isascii() or any(ord(c)<33 or ord(c)>126 for c in url)):
            raise ProjectError('Web URL must be absolute printable ASCII HTTPS <=192 bytes')
    else:
        if 'url' in obj or 'content' not in obj:
            raise ProjectError('Text/Lua apps require content and forbid url')
        assets['content']=within_project(project,obj['content'])
        n=assets['content'].stat().st_size
        if n<1 or n>(64*1024 if kind=='lua' else MAX_TEXT):
            raise ProjectError('Source/payload invalid size; Lua <=64 KiB, text <=256 KiB')
        if kind=='lua':
            data=assets['content'].read_bytes()
            if b'\x00' in data or assets['content'].suffix.lower()!='.lua':
                raise ProjectError('Lua source must be .lua text, not bytecode')
            try:data.decode('utf-8')
            except UnicodeDecodeError as err:
                raise ProjectError('Lua source must be UTF-8') from err
    if 'icon' in obj:
        assets['icon']=within_project(project,obj['icon'])
        try:
            from PIL import Image
        except ImportError as err:
            raise ProjectError('Pillow required for optional icon PNG') from err
        with Image.open(assets['icon']) as im:
            if im.format != 'PNG' or im.size != (32,32):
                raise ProjectError('Icon must be PNG exactly 32x32')
    return obj,assets

def build(args) -> int:
    obj, assets=validate(args.project)
    signer=args.firmware_root.resolve(strict=True)/'tools'/'build_qeapp.py'
    if not signer.is_file():
        raise ProjectError(f'Missing firmware signer: {signer}')
    key=args.sign_key.resolve(strict=True)
    if not key.is_file():
        raise ProjectError('Signing key not found')
    cmd=[sys.executable,str(signer),'--id',obj['id'],'--name',obj['name'],'--version',obj['version'],
         '--type',obj['type'],'--sign-key',str(key),'--key-id',hex(args.key_id if args.key_id is not None else (0x544c5541 if obj['type']=='lua' else 0x31534351)),'-o',str(args.output.resolve())]
    if obj['type']=='text':
        cmd+=['--text',str(assets['content'])]
    elif obj['type']=='lua':
        if not args.experimental_lua:
            raise ProjectError('Lua package needs --experimental-lua and vqeaf_lua_beta firmware')
        if not (args.firmware_root/'src/lua/QeLuaRuntime.cpp').is_file():
            raise ProjectError('Selected firmware lacks experimental Lua VM support')
        cmd+=['--lua',str(assets['content']),'--enable-lua-experimental']
    else:
        cmd+=['--url',obj['url']]
    if 'icon' in assets:
        cmd+=['--icon',str(assets['icon'])]
    print('Executing verified firmware QEAPP/2 builder (signing key path omitted)')
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if proc.returncode:
        # Some external signer diagnostics may contain the key path: never echo raw stderr.
        print('Firmware signer failed; check project values, dependencies and local signing configuration',file=sys.stderr)
        return proc.returncode
    print(f'Created signed package: {args.output.resolve()}')
    return 0

def inspect(file: Path, public_key: Path|None=None, key_id: int|None=None) -> dict:
    data=file.read_bytes()
    if len(data)<116+76 or data[:8]!=MAGIC:
        raise ProjectError('Not a QEAPP/2 binary file')
    m,i,p=struct.unpack_from('<III', data, 8)
    if m<1 or m>2048 or i not in (0,2048) or p>MAX_TEXT:
        raise ProjectError('Package section lengths invalid')
    total=116+m+i+p+76
    if total!=len(data):
        raise ProjectError('Package truncated or has extra bytes')
    pos=116
    for n,digest,label in ((m,data[20:52],'manifest'),(i,data[52:84],'icon'),(p,data[84:116],'payload')):
        section=data[pos:pos+n]
        if hashlib.sha256(section).digest()!=digest:
            raise ProjectError(f'{label} SHA-256 mismatch')
        pos+=n
    manifest=data[116:116+m].decode('ascii','strict')
    fields={}
    for line in manifest.splitlines():
        if not line: continue
        if '=' not in line:raise ProjectError('Malformed manifest line')
        k,v=line.split('=',1)
        if k in fields:raise ProjectError('Duplicate manifest key')
        fields[k]=v
    if fields.get('type') not in ('text','web','lua') or set(fields)-{'id','name','version','type','entry'}:
        raise ProjectError('Manifest unsupported type or keys')
    if not all(k in fields for k in ('id','name','version')):
        raise ProjectError('Incomplete manifest')
    if not re.fullmatch(r'[a-z0-9_-]{1,24}',fields['id']):
        raise ProjectError('Invalid package app id')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*',fields['version']) or len(fields['version'])>19:
        raise ProjectError('Invalid package version')
    if not 1<=len(fields['name'])<=40 or any(ord(c)<32 or ord(c)>126 for c in fields['name']):
        raise ProjectError('Invalid package name')
    if fields['type']=='web':
        if 'entry' not in fields or not fields['entry'].startswith('https://') or p!=0:
            raise ProjectError('Invalid web package entry or payload')
    elif 'entry' in fields or p==0 or (fields['type']=='lua' and p>64*1024):
        raise ProjectError('Invalid script/text package entry or payload')
    trailer=data[-76:]
    if trailer[:8]!=TRAILER_MAGIC:
        raise ProjectError('QEAPP/2 signature trailer missing')
    signed_id=struct.unpack_from('<I',trailer,8)[0]
    info={'size':len(data),'id':fields.get('id'),'version':fields.get('version'),
          'type':fields['type'],'key_id':hex(signed_id), 'section_sha256':'PASS',
          'signature':'NOT_CHECKED (provide --public-key)'}
    if public_key:
        if key_id is not None and signed_id!=key_id:
            raise ProjectError(f'Signing key ID mismatch: package {hex(signed_id)}, expected {hex(key_id)}')
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec, utils
            from cryptography.exceptions import InvalidSignature
        except ImportError as err:
            raise ProjectError('cryptography package required for signature verification') from err
        pub=serialization.load_pem_public_key(public_key.read_bytes())
        if not isinstance(pub, ec.EllipticCurvePublicKey) or pub.curve.name!='secp256r1':
            raise ProjectError('Expected P-256 public key')
        r=int.from_bytes(trailer[12:44],'big')
        s=int.from_bytes(trailer[44:76],'big')
        try:
            pub.verify(utils.encode_dss_signature(r,s),hashlib.sha256(data[:-76]).digest(),ec.ECDSA(utils.Prehashed(hashes.SHA256())))
        except InvalidSignature as err:
            raise ProjectError('Digital signature verification failed') from err
        info['signature']='PASS (against supplied PEM only)'
    return info

def init_project(template: str, destination: Path, app_id: str, name: str) -> None:
    src=Path(__file__).resolve().parents[1]/'projects'/({'text':'text-notes','web':'web-bookmark','lua':'lua-hello','lua-snake':'lua-snake','lua-sprite':'lua-sprite'}[template])
    if destination.exists():
        raise ProjectError('Destination exists; refusing to overwrite')
    if not re.fullmatch(r'[a-z0-9_-]{1,24}',app_id):
        raise ProjectError('New project ID invalid')
    if not name or len(name)>40 or not name.isascii() or any(ord(c)<32 or ord(c)>126 for c in name):
        raise ProjectError('New project name must be printable ASCII (1..40)')
    shutil.copytree(src,destination)
    cfg=destination/'qeapp.project.json'
    obj=json.loads(cfg.read_text(encoding='utf-8'))
    obj['id'],obj['name']=app_id,name
    cfg.write_text(json.dumps(obj,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
    validate(destination)

def parse():
    cli=argparse.ArgumentParser(description='QEAPP Studio v0.5: signed text/web + opt-in Lua beta and 1-bit sprite preview')
    sub=cli.add_subparsers(dest='cmd',required=True)
    new=sub.add_parser('init');new.add_argument('--template',choices=['text','web','lua','lua-snake','lua-sprite'],required=True)
    new.add_argument('--id',required=True);new.add_argument('--name',required=True)
    new.add_argument('-o','--output',type=Path,required=True)
    d=sub.add_parser('doctor');d.add_argument('--firmware-root',type=Path,required=True)
    v=sub.add_parser('validate');v.add_argument('project',type=Path)
    b=sub.add_parser('build');b.add_argument('project',type=Path)
    b.add_argument('--firmware-root',type=Path,required=True)
    b.add_argument('--sign-key',type=Path,required=True)
    b.add_argument('--experimental-lua',action='store_true',help='Explicit opt-in; requires vqeaf_lua_beta firmware')
    b.add_argument('--key-id',type=lambda x:int(x,0),default=None)
    b.add_argument('-o','--output',type=Path,required=True)
    i=sub.add_parser('inspect');i.add_argument('package',type=Path)
    i.add_argument('--public-key',type=Path)
    i.add_argument('--key-id',type=lambda x:int(x,0))
    t=sub.add_parser('test');t.add_argument('--firmware-root',type=Path)
    q=sub.add_parser('lua-preview',help='Run bounded Lua 5.4 VM on PC and export PNG')
    q.add_argument('project',type=Path)
    q.add_argument('--frames',type=int,default=8)
    q.add_argument('--replay',type=Path,help='Project-relative tests/input_replay.json')
    q.add_argument('-o','--output',type=Path,required=True)
    s=sub.add_parser('simulate',help='M1 host-only Snake preview (NOT a QEAPP build)')
    s.add_argument('--demo',choices=['snake','hello'],default='snake')
    s.add_argument('--scenario',choices=['ready','playing','paused'],default='playing')
    s.add_argument('--frames',type=int,default=40)
    s.add_argument('-o','--output',type=Path,required=True)
    return cli.parse_args()

def main()->int:
    args=parse()
    try:
        if args.cmd=='init':
            init_project(args.template,args.output,args.id,args.name)
            print(f'Created {args.template} project: {args.output.resolve()}')
        elif args.cmd=='test':
            env=os.environ.copy()
            if args.firmware_root:
                env['QEAPP_FIRMWARE_ROOT']=str(args.firmware_root.resolve(strict=True))
            return subprocess.call([sys.executable,'-m','unittest','discover','-s',
                str(Path(__file__).resolve().parents[1]/'tests'),'-v'],env=env)
        elif args.cmd=='validate':
            obj, assets=validate(args.project)
            print(json.dumps({'status':'VALID','type':obj['type'],'id':obj['id'],
                'assets':list(assets)},indent=2))
        elif args.cmd=='build':
            return build(args)
        elif args.cmd=='inspect':
            print(json.dumps(inspect(args.package,args.public_key,args.key_id),indent=2))
        elif args.cmd=='lua-preview':
            obj, assets = validate(args.project)
            if obj['type']!='lua':raise ProjectError('Open a type=lua project to preview Lua')
            cmd=[sys.executable,str(Path(__file__).with_name('lua_preview.py')),
                str(assets['content']),'--frames',str(args.frames),'--output',str(args.output)]
            if args.replay is not None:
                if args.replay.is_absolute():
                    raise ProjectError('Replay path must be relative to project')
                replay=within_project(args.project,args.replay.as_posix())
                if replay.suffix.lower()!='.json':
                    raise ProjectError('Replay path must have .json suffix')
                cmd += ['--replay',str(replay)]
            return subprocess.call(cmd)
        elif args.cmd=='simulate':
            return subprocess.call([sys.executable,str(Path(__file__).with_name('simulate_host.py')),
                '--demo',args.demo,'--scenario',args.scenario,'--frames',str(args.frames),'--out',str(args.output)])
        elif args.cmd=='doctor':
            root=args.firmware_root.resolve(strict=True)
            missing=[p for p in ('tools/build_qeapp.py','tools/qeapp_keys.py',
              'src/services/QeappFormat.cpp','src/services/QeappTrustKey.h',
              'docs/QEAPP_V15_SIGNING.md') if not (root/p).is_file()]
            if missing:raise ProjectError('Firmware checkout missing: '+', '.join(missing))
            print('PASS: detected signed QEAPP/2 firmware toolchain (does NOT verify hardware build)')
    except (ProjectError,OSError,UnicodeError,ValueError) as err:
        print(f'ERROR: {err}',file=sys.stderr)
        return 2
    return 0

if __name__=='__main__':
    sys.exit(main())
