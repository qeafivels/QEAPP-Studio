"""Non-destructive environment checks and opt-in per-user settings repair.

Never touch project source, signing keys, firmware, .venv or installed packages.
Run `inspect()` before `apply()`; only corrupt settings.json is backed up.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def settings_path() -> Path:
    base = Path(os.getenv('APPDATA') or os.getenv('XDG_CONFIG_HOME') or Path.home()/'.config')
    return base / 'QEAPPStudio' / 'settings.json'


@dataclass
class Check:
    name: str
    status: str   # PASS | WARN | FAIL
    detail: str
    repairable: bool = False


def inspect(settings: Path | None = None, root: Path = ROOT, *, qt_probe: bool = True) -> list[Check]:
    settings = Path(settings) if settings is not None else settings_path()
    out = []
    out.append(Check('Python', 'PASS' if sys.version_info >= (3, 10) else 'FAIL', sys.version.split()[0]))
    for pkg in ('PySide6', 'PIL', 'cryptography'):
        out.append(Check(pkg, 'PASS' if importlib.util.find_spec(pkg) else 'WARN',
                         'Python import found' if importlib.util.find_spec(pkg) else 'Missing; use run_studio.bat'))
    if qt_probe and importlib.util.find_spec('PySide6') is not None:
        env = dict(os.environ)
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None)
        env.pop('QT_PLUGIN_PATH', None)
        smoke = ('from PySide6.QtWidgets import QApplication; '
                 'from PySide6.QtGui import QImage; '
                 'app=QApplication([]); '
                 'img=QImage(240,320,QImage.Format_RGB16); '
                 'assert not img.isNull(); app.quit()')
        try:
            proc = subprocess.run([sys.executable,'-c',smoke],env=env,
                capture_output=True,text=True,timeout=10)
            out.append(Check('Qt offscreen smoke', 'PASS' if proc.returncode == 0 else 'WARN',
                'Qt QApplication + RGB565 QImage work' if proc.returncode == 0 else
                f'Qt exited {proc.returncode}; inspect logs/launcher.log for plugin/DLL details'))
        except (OSError, subprocess.TimeoutExpired):
            out.append(Check('Qt offscreen smoke','WARN','Qt subprocess unavailable or timed out'))
    else:
        out.append(Check('Qt offscreen smoke','WARN','Not run: PySide6 missing or active GUI already running'))
    lua = (Path(os.environ['QEAPP_FIRMWARE_ROOT']) if os.environ.get('QEAPP_FIRMWARE_ROOT') else (root.parent/'VQEAF-OS' if (root.parent/'VQEAF-OS/platformio.ini').is_file() else root/'firmware/VQEAF-OS')) / 'lib/VqeafLua54/src/lua.h'
    vm = root / 'build' / ('qe_lua_host.exe' if os.name == 'nt' else 'qe_lua_host')
    out.append(Check('Lua source', 'PASS' if lua.is_file() else 'WARN',
                     'Installed' if lua.is_file() else 'Missing: --setup-lua'))
    out.append(Check('Host VM', 'PASS' if vm.is_file() else 'WARN',
                     'Available' if vm.is_file() else 'Missing: --build-vm'))
    for name, cmd in (('C compiler', 'gcc'), ('C++ compiler', 'g++')):
        ok = shutil.which(cmd) is not None
        out.append(Check(name, 'PASS' if ok else 'WARN', 'Available' if ok else 'Missing from PATH'))
    if not settings.exists():
        out.append(Check('User settings', 'PASS', 'Default settings; no existing file'))
    else:
        try:
            raw = settings.read_bytes()
            if len(raw) > 128 * 1024:
                raise ValueError('Settings file exceeds 128 KiB')
            obj = json.loads(raw.decode('utf-8'))
            if not isinstance(obj, dict) or any(k not in ('recent_projects','firmware_root','last_open_folder') for k in obj):
                raise ValueError('Invalid setting keys')
            if ('recent_projects' in obj and (not isinstance(obj['recent_projects'], list) or
                    len(obj['recent_projects']) > 8 or any(not isinstance(p,str) or len(p)>2048 for p in obj['recent_projects']))):
                raise ValueError('Invalid recent projects')
            for field in ('firmware_root', 'last_open_folder'):
                if field in obj and (not isinstance(obj[field], str) or len(obj[field])>2048):
                    raise ValueError('Invalid path value')
            out.append(Check('User settings', 'PASS', 'JSON schema valid'))
        except (OSError, UnicodeError, ValueError) as exc:
            out.append(Check('User settings', 'WARN', f'Corrupt settings: {type(exc).__name__}', True))
    return out


def apply(settings: Path | None = None) -> Path | None:
    """Backup corrupt settings first, then atomically replace only those settings."""
    settings = Path(settings) if settings is not None else settings_path()
    if not any(x.name == 'User settings' and x.repairable for x in inspect(settings, qt_probe=False)):
        return None
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = settings.with_name(settings.name + '.backup-' + stamp)
    # same directory atomic move; never overwrite existing backup
    if backup.exists() or not settings.is_file():
        raise FileExistsError('Settings changed; rerun doctor before applying repair')
    settings.rename(backup)
    try:
        from studio.core.config import StudioConfig
        StudioConfig(settings).update(recent_projects=[], firmware_root='', last_open_folder='')
    except Exception:
        # Preserve original settings if replacing file fails.
        settings.unlink(missing_ok=True)
        backup.rename(settings)
        raise
    return backup


def as_json(checks: list[Check]) -> str:
    return json.dumps({'checks':[asdict(x) for x in checks]}, indent=2)
