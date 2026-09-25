"""Bounded local diagnostics for the QEAPP host IDE; never capture source or keys."""
from __future__ import annotations
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGDIR = ROOT / 'logs'
MAX_LOG_BYTES = 1_000_000
# Only lua error position and summary are relayed; do not parse arbitrary paths.
_GUEST_LINE = re.compile(r'(?:signed-qeapp-main\.lua|main\.lua):([1-9]\d{0,5}):\s*(.{0,250})')


def guest_error(text: str) -> tuple[int, str] | None:
    if not isinstance(text, str) or len(text) > 2048:
        return None
    match = _GUEST_LINE.search(text)
    return (int(match.group(1)), match.group(2)) if match else None


def _rotate(path: Path) -> None:
    if path.is_file() and path.stat().st_size > MAX_LOG_BYTES:
        path.replace(path.with_suffix('.previous.log'))


def write_error(kind: str, text: str, path: Path | None = None) -> Path:
    """Local crash report. Bounded; traceback body is not a dump of project files."""
    path = path or LOGDIR / 'gui-errors.log'
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate(path)
    kind = re.sub(r'[^A-Za-z0-9_-]', '_', kind[:30])
    with path.open('a', encoding='utf-8') as log:
        log.write(datetime.now(timezone.utc).isoformat() + ' [' + kind + '] ' + text[:8000] + '\n')
    return path


class DebugSession:
    """Opt-in VM events only. No project paths, script text, environment or credentials."""
    EVENTS = frozenset({'start', 'stop', 'pause', 'resume', 'step', 'key', 'frame', 'vm_error', 'watchdog'})

    def __init__(self, directory: Path = LOGDIR):
        directory.mkdir(parents=True, exist_ok=True)
        name = datetime.now(timezone.utc).strftime('vm-%Y%m%dT%H%M%S%fZ')
        self.path = directory / (name + '.jsonl')
        self.count = 0
        self.active = True

    def record(self, event: str, **values) -> None:
        if not self.active or self.count >= 6000 or event not in self.EVENTS:
            return
        # Accept only safe numeric/boolean fields and fixed key names; never
        # serialize guest script, Lua errors or selected file paths into logs.
        safe = {}
        for key, value in values.items():
            if key in ('frame', 'heap', 'response_ms', 'fps', 'cap_kib', 'exit_code') and isinstance(value, (int, float)):
                safe[key] = max(-1_000_000, min(1_000_000, value))
            if key == 'key' and value in ('up', 'down', 'left', 'right', 'start', 'option'):
                safe[key] = value
            if key == 'down' and isinstance(value, bool):
                safe[key] = value
        record = {'timestamp': datetime.now(timezone.utc).isoformat(), 'event': event, **safe}
        _rotate(self.path)
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, separators=(',', ':')) + '\n')
        self.count += 1

    def stop(self):
        self.active = False


def install_exception_hook(notify=None):
    """Log unexpected Python/Qt slot errors instead of silent GUI disappearance."""
    previous = sys.excepthook
    busy = False
    def hook(typ, value, tb):
        nonlocal busy
        if typ is KeyboardInterrupt:
            previous(typ, value, tb)
            return
        if busy:
            previous(typ, value, tb)
            return
        busy = True
        try:
            detail = ''.join(traceback.format_exception(typ, value, tb))
            path = write_error('unhandled_gui', detail)
            if notify is not None:
                try:
                    notify(f'GUI exception recorded in {path.name}; see Diagnostics.')
                except Exception:
                    pass
        except Exception:
            previous(typ, value, tb)
        finally:
            busy = False
    sys.excepthook = hook
    return previous
