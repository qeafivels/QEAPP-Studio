"""Isolated, non-relocating virtualenv slots with validated atomic activation.

Never copy/move a venv on Windows: pip.exe entry points encode absolute paths.
Promotion changes only a small JSON pointer after all checks pass; previous
runtime and every user project are retained. Staging uses a unique new folder.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import time

# A fixed relative whitelist ensures state corruption cannot execute an arbitrary
# interpreter path if logs/active-runtime.json is edited or becomes damaged.
_SLOT = re.compile(r'^\.qeapp_envs/[a-z0-9][a-z0-9_-]{4,70}$')
ACTIVE = 'active'
PREVIOUS = 'previous'


def permitted_relative(value: object) -> bool:
    return value == '.venv' or (isinstance(value, str) and _SLOT.fullmatch(value) is not None)


def runtime_directory(root: Path, rel: str) -> Path:
    if not permitted_relative(rel):
        raise ValueError('Invalid runtime path in pointer')
    candidate = root / Path(rel)
    # Do not accept symlink escapes or an outside path.
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError('Runtime resolves outside project root')
    return candidate


def load_pointer(root: Path) -> dict:
    path = root / 'logs' / 'active-runtime.json'
    try:
        val = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(val, dict) or not permitted_relative(val.get(ACTIVE)):
            return {}
        runtime_directory(root, val[ACTIVE])
        prev = val.get(PREVIOUS)
        if prev is not None:
            runtime_directory(root, prev)
        return val
    except (OSError, ValueError, TypeError, UnicodeError):
        return {}


def atomic_pointer(root: Path, active: str, previous: str | None, *, reason: str) -> None:
    runtime_directory(root, active)
    if previous is not None:
        runtime_directory(root, previous)
    target = root / 'logs' / 'active-runtime.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.pending.json')
    state = {'schema': 1, ACTIVE: active, PREVIOUS: previous,
             'reason': reason, 'switched_utc': datetime.now(timezone.utc).isoformat()}
    # Neither path contains user data/keys; no venv directory is moved.
    try:
        with tmp.open('w', encoding='utf-8') as fd:
            json.dump(state, fd, indent=2, sort_keys=True)
            fd.write('\n')
            fd.flush()
            os.fsync(fd.fileno())
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)


def new_slot(root: Path, *, now: datetime | None = None, pid: int | None = None) -> tuple[str, Path]:
    now = now or datetime.now(timezone.utc)
    pid = os.getpid() if pid is None else pid
    name = 'env-' + now.strftime('%Y%m%dt%H%M%S%f') + '-' + str(pid)
    relative = '.qeapp_envs/' + name
    directory = runtime_directory(root, relative)
    if directory.exists():
        raise FileExistsError('Staging runtime already exists')
    return relative, directory


def cleanup_failed_stage(root: Path, rel: str) -> None:
    """Only remove a transient slot we generated, never active/previous/.venv."""
    ptr = load_pointer(root)
    if rel in (ptr.get(ACTIVE), ptr.get(PREVIOUS)):
        return
    # Refuse cleanup outside the dedicated staging namespace.
    if not (rel.startswith('.qeapp_envs/env-') and permitted_relative(rel)):
        return
    d = runtime_directory(root, rel)
    if d.exists() and not d.is_symlink():
        shutil.rmtree(d)


class UpdateLocked(RuntimeError):
    """Raised when another Studio instance is installing a staged runtime."""


class update_lock:
    """Single-writer guard with an exclusive creation, keeping other GUIs usable.

    Lock is created only for dependency staging, not for ordinary IDE startup.
    No automatic deletion of a possibly live lock (a stale one can be manually
    removed after verifying no other updater is running).
    """
    def __init__(self, root: Path):
        self.path = root / 'logs' / 'runtime-update.lock'
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise UpdateLocked('Another safe update is active. If no updater is '
                               'running, inspect/remove logs/runtime-update.lock.') from exc
        self.acquired = True
        try:
            with os.fdopen(fd, 'w', encoding='ascii') as handle:
                handle.write(f'pid={os.getpid()} started={int(time.time())}\n')
        except OSError:
            self.path.unlink(missing_ok=True)
            self.acquired = False
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False
        return False
