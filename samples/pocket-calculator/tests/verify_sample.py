#!/usr/bin/env python3
"""Deterministic host-only tests for Pocket Calculator. No device/GPU claims."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path

# Monorepo checkout: firmware is at the VQEAF-OS repository root, not a duplicated copy.
# For a standalone Studio checkout, allow QEAPP_FIRMWARE_ROOT to point to firmware.
def firmware_root(studio:Path):
    override=os.environ.get('QEAPP_FIRMWARE_ROOT')
    if override:return Path(override).expanduser().resolve()
    candidate=studio.parent.parent
    if (candidate/'tools/build_qeapp.py').is_file():return candidate
    legacy=studio/'firmware/VQEAF-OS'
    if legacy.is_dir():return legacy
    raise RuntimeError('VQEAF OS firmware source missing; set QEAPP_FIRMWARE_ROOT')
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'projects/pocket-calculator-lua'
GUIDE=ROOT/'projects/pocket-calculator-guide'
SCENARIOS=('home','calculator','result_7_plus_2','history_result','divide_by_zero','clear_error','about','empty_history')

def run(args,env=None,timeout=120):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=timeout)
    if r.returncode:
        raise RuntimeError(f'{args[0]} returned {r.returncode}: {r.stdout[-500:]} {r.stderr[-1000:]}')
    return r.stdout

def main(studio,system_lua=False):
    from PIL import Image
    studio=studio.resolve(strict=True)
    q=studio/'tools/qstudio.py';preview=studio/'tools/lua_preview.py'
    if not q.is_file() or not preview.is_file():
        raise FileNotFoundError('Provide QEAPP Studio v0.7.4 source root')
    result={'test_environment':'Linux/Windows PC host','device':'NOT TESTED','qt_gui':'NOT TESTED',
            'tests':[],'screenshots':{}}
    for name,project in (('Lua',APP),('Stock guide',GUIDE)):
        output=json.loads(run([sys.executable,q,'validate',project]))
        assert output['status']=='VALID'
        result['tests'].append(f'{name} project validation PASS')
    env=os.environ.copy()
    if system_lua: env['QEAPP_HOST_SYSTEM_LUA']='1'
    binary=studio/'build'/('qe_lua_host.exe' if os.name=='nt' else 'qe_lua_host')
    if not binary.is_file():
        run([sys.executable,studio/'tools/build_lua_host.py']+(['--system-lua'] if system_lua else []),timeout=180)
    for name in SCENARIOS:
        screen=ROOT/'screenshots'/f'{name}.png'
        output=json.loads(run([sys.executable,preview,APP/'main.lua','--frames','40',
                               '--replay',APP/'tests'/f'{name}.json','-o',screen],env=env))
        assert output['status']=='LUA_HOST_PASS' and output['replayed_input_events']>0
        with Image.open(screen) as im:assert im.size==(240,320)
        result['tests'].append(f'Actual Lua host 40 frames {name}: PASS')
        result['screenshots'][name]={'sha256':hashlib.sha256(screen.read_bytes()).hexdigest(),
                                      'frames':output['frames'],'log':output['runtime_log']}
    with Image.open(ROOT/'screenshots/divide_by_zero.png') as im:
        pixel=im.convert('RGB').getpixel((9,29+57))
        assert pixel[0]>pixel[1]*2, f'Missing red error border: {pixel}'
    with Image.open(ROOT/'screenshots/clear_error.png') as im:
        pixel=im.convert('RGB').getpixel((9,29+57))
        assert pixel[2]>pixel[0],f'Clear did not reset error border: {pixel}'
    with Image.open(ROOT/'screenshots/history_result.png') as im:
        pixel=im.convert('RGB').getpixel((8,29+86))
        assert pixel[2]>pixel[0]*1.4,f'History row not highlighted: {pixel}'
    result['tests'].extend(['Division-by-zero red error UI PASS','Clear error reset UI PASS','History selection UI PASS'])
    # Real stock .qeapp sign/verify with ephemeral ECDSA key; never store keys/packages in sample.
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    with tempfile.TemporaryDirectory(prefix='pocketcalc-sign-') as td:
        tmp=Path(td)
        sk=ec.generate_private_key(ec.SECP256R1())
        priv,pub=tmp/'private.pem',tmp/'public.pem'
        priv.write_bytes(sk.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
        pub.write_bytes(sk.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo))
        for name,project,keyid,extra in (
            ('Stock text guide',GUIDE,'0x31534351',[]),
            ('Lua beta',APP,'0x544c5541',['--experimental-lua'])):
            pkg=tmp/(name.replace(' ','_')+'.qeapp')
            run([sys.executable,q,'build',project,'--firmware-root',firmware_root(studio),
                 '--sign-key',priv,'--key-id',keyid,'-o',pkg,*extra])
            summary=json.loads(run([sys.executable,q,'inspect',pkg,'--public-key',pub,'--key-id',keyid]))
            assert summary['section_sha256']=='PASS' and summary['signature'].startswith('PASS')
            result['tests'].append(f'{name} ephemeral host signing and verify PASS')
    report=ROOT/'reports/host_test_results.json';report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'result':'HOST PASS','count':len(result['tests']),'device':'NOT TESTED',
                      'qt_gui':'NOT TESTED','report':str(report)},indent=2))
    return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--studio',required=True,type=Path)
    ap.add_argument('--system-lua',action='store_true');args=ap.parse_args()
    try: main(args.studio,args.system_lua)
    except (OSError,RuntimeError,ValueError,AssertionError,subprocess.TimeoutExpired) as exc:
        print('FAIL',exc,file=sys.stderr);raise SystemExit(1)
