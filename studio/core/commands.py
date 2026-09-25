"""Only invokes the original qstudio CLI; never reimplements package signing."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools' / 'qstudio.py'

@dataclass(frozen=True)
class JobSpec:
    argv: list[str]
    label: str
    preview: Path | None = None
    secrets: tuple[str, ...] = ()
    timeout: float = 240


def validate(project: Path) -> JobSpec:
    return JobSpec([sys.executable, str(CLI), 'validate', str(project)], 'Validate project', timeout=30)


def build(project: Path, firmware: Path, key_file: Path, output: Path, key_id: int, experimental_lua: bool = False) -> JobSpec:
    if not 0 <= key_id <= 0xFFFFFFFF:
        raise ValueError('Invalid key ID')
    argv=[sys.executable, str(CLI), 'build', str(project),
        '--firmware-root', str(firmware), '--sign-key', str(key_file),
        '--key-id', hex(key_id), '-o', str(output)]
    if experimental_lua:argv+=['--experimental-lua']
    return JobSpec(argv,
        'Experimental signed Lua QEAPP/2 build' if experimental_lua else 'Signed QEAPP/2 build',
        secrets=(str(key_file),), timeout=120)


def inspect(package: Path, public_key: Path | None = None, key_id: int | None = None) -> JobSpec:
    argv = [sys.executable, str(CLI), 'inspect', str(package)]
    if public_key is not None:
        argv += ['--public-key', str(public_key)]
    if key_id is not None:
        argv += ['--key-id', hex(key_id)]
    return JobSpec(argv, 'Inspect QEAPP/2 package', timeout=30)


def simulate(demo: str, scenario: str, screenshot: Path, frames: int = 40) -> JobSpec:
    if demo not in ('snake', 'hello') or scenario not in ('ready', 'playing', 'paused'):
        raise ValueError('Unknown host demo/scenario')
    if frames < 0 or frames > 2000:
        raise ValueError('Frames out of range')
    return JobSpec([sys.executable, str(CLI), 'simulate', '--demo', demo,
        '--scenario', scenario, '--frames', str(frames), '-o', str(screenshot)],
        f'HOST simulator {demo} (not a device QEAPP)', preview=screenshot, timeout=150)


def doctor(firmware: Path) -> JobSpec:
    return JobSpec([sys.executable, str(CLI), 'doctor', '--firmware-root', str(firmware)],
        'Check firmware signer availability', timeout=30)


def tests(firmware: Path | None = None) -> JobSpec:
    argv = [sys.executable, str(CLI), 'test']
    if firmware is not None:
        argv += ['--firmware-root', str(firmware)]
    return JobSpec(argv, 'Run host regression tests', timeout=240)


def lua_preview(project: Path, screenshot: Path, frames: int = 8) -> JobSpec:
    if type(frames) is not int or not 1 <= frames <= 200:
        raise ValueError('Lua replay frames must be 1..200')
    argv=[sys.executable, str(CLI), 'lua-preview', str(project),
          '--frames',str(frames),'-o',str(screenshot)]
    # Default project replay exercises the real VM input callback and renderer.
    # CLI validates the path inside the current workspace before reading it.
    if (project/'tests/input_replay.json').is_file():
        argv+=['--replay','tests/input_replay.json']
    return JobSpec(argv,
                   'Bounded Lua 5.4 host VM (NOT device)', preview=screenshot, timeout=180)


def beta_preflight(firmware: Path) -> JobSpec:
    return JobSpec([sys.executable, str(ROOT / 'tools/device_preflight.py'), '--firmware-root', str(firmware)],
        'Lua beta device preflight (not an upload)', timeout=20)


def build_lua_host() -> JobSpec:
    """Build desktop Lua runner with the same VM source as beta ESP32 runtime."""
    import os
    argv = [sys.executable, str(ROOT/'tools/build_lua_host.py')]
    if os.environ.get('QEAPP_HOST_SYSTEM_LUA') == '1':
        argv += ['--system-lua']
    return JobSpec(argv, 'Build Lua host virtual-phone runner', timeout=180)
