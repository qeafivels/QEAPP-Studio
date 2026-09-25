"""Bounded and sandboxed UTF-8 project editing for QEAPP Studio.

No symlink traversal, no private key editing, no implicit overwrite of external
changes, and atomic replace on save. This module deliberately has no Qt deps.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import struct
import tempfile

MAX_EDITOR_BYTES = 1_048_576
ALLOWED_EXTENSIONS = frozenset({
    '.txt', '.json', '.md', '.lua', '.py', '.c', '.cpp', '.h', '.hpp',
    '.html', '.css', '.js', '.ini', '.toml', '.yaml', '.yml', '.xml', '.csv',
})
FORBIDDEN_NAMES = frozenset({
    '.git', '.venv', '__pycache__', 'dist', 'build', 'node_modules',
    'id_rsa', 'id_ed25519', 'private_key', 'private.pem',
})
FORBIDDEN_EXTENSIONS = frozenset({'.pem', '.key', '.p12', '.pfx', '.qeapp'})

class WorkspaceError(ValueError):
    """User-visible project filesystem safety / merge error."""

@dataclass(frozen=True)
class Document:
    relative_path: str
    text: str
    sha256: str


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Workspace:
    def __init__(self, project: Path):
        project = Path(project).resolve(strict=True)
        if not project.is_dir() or not (project / 'qeapp.project.json').is_file():
            raise WorkspaceError('Select a folder containing qeapp.project.json')
        if (project / 'qeapp.project.json').is_symlink():
            raise WorkspaceError('Symlink project metadata is forbidden')
        self.root = project

    def path(self, rel: str, *, create: bool = False) -> Path:
        if not rel or not isinstance(rel, str) or '\\' in rel or '\x00' in rel or rel.startswith('/'):
            raise WorkspaceError('Expected relative POSIX project path')
        pp = PurePosixPath(rel)
        if not pp.parts or any(part in ('.', '..') or part.startswith('.') for part in pp.parts):
            # Dotfiles and hidden folders are deliberately inaccessible to editor.
            raise WorkspaceError('Hidden/parent path components are forbidden')
        if any(part.casefold() in FORBIDDEN_NAMES for part in pp.parts):
            raise WorkspaceError('Build/cache/key paths are not editable')
        if pp.suffix.casefold() not in ALLOWED_EXTENSIONS or pp.suffix.casefold() in FORBIDDEN_EXTENSIONS:
            raise WorkspaceError('Only approved UTF-8 source/text assets are editable')
        path = self.root.joinpath(*pp.parts)
        cursor = self.root
        for part in pp.parts:
            cursor = cursor / part
            if cursor.is_symlink():
                raise WorkspaceError('Symlinks are not allowed inside editor paths')
        try:
            path.resolve(strict=False).relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceError('Path escapes project root') from exc
        if create:
            if not path.parent.is_dir():
                raise WorkspaceError('Create the parent folder before a file')
        elif not path.is_file():
            raise WorkspaceError('Source file not found')
        if path.exists() and not stat.S_ISREG(path.stat().st_mode):
            raise WorkspaceError('Expected a regular file')
        return path

    def read_png_preview(self, rel: str) -> bytes:
        """Safely expose small PNG bytes from the project for a desktop-only preview.

        Binary assets may be inspected, but never opened by the UTF-8 editor.
        Deliberately reject symlinks, hidden/key/build folders and large geometry.
        Qt renders memory bytes only after these checks; no decoder on ESP32.
        """
        if not isinstance(rel, str) or not rel.lower().endswith('.png'):
            raise WorkspaceError('Only .png preview assets are supported')
        # Reuse the source path security policy without adding binary edit access.
        from pathlib import PurePosixPath
        pp = PurePosixPath(rel)
        if ('\\' in rel or rel.startswith('/') or not pp.parts or
                any(x in ('.','..') or x.startswith('.') or x.casefold() in FORBIDDEN_NAMES
                    for x in pp.parts)):
            raise WorkspaceError('Unsafe PNG project path')
        current = self.root
        for part in pp.parts:
            current /= part
            if current.is_symlink():
                raise WorkspaceError('Symlink PNG assets are forbidden')
        try:
            current.resolve(strict=True).relative_to(self.root)
        except (OSError, ValueError) as exc:
            raise WorkspaceError('PNG asset must remain inside project') from exc
        if not current.is_file() or current.stat().st_size > 1024*1024:
            raise WorkspaceError('PNG preview requires a regular file <= 1 MiB')
        raw = current.read_bytes()
        if len(raw) < 33 or raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR':
            raise WorkspaceError('Invalid PNG preview header')
        width, height = struct.unpack('>II',raw[16:24])
        if not 1 <= width <= 512 or not 1 <= height <= 512:
            raise WorkspaceError('PNG preview must be 1..512 pixels per axis')
        return raw

    def mkdir(self, rel: str) -> Path:
        """Create a source/asset directory inside the project; no hidden or symlink segments."""
        if not rel or not isinstance(rel, str) or '\\' in rel or '\x00' in rel or rel.startswith('/'):
            raise WorkspaceError('Expected relative POSIX folder path')
        parts = PurePosixPath(rel).parts
        if not parts or any(p in ('.', '..') or p.startswith('.') or p.casefold() in FORBIDDEN_NAMES for p in parts):
            raise WorkspaceError('Unsafe folder path')
        cursor = self.root
        for segment in parts[:-1]:
            cursor /= segment
            if cursor.is_symlink() or not cursor.is_dir():
                raise WorkspaceError('Folder parent is missing or symlinked')
        result = cursor / parts[-1]
        if result.exists() or result.is_symlink():
            raise WorkspaceError('Folder already exists')
        result.mkdir()
        return result

    def read(self, rel: str) -> Document:
        path = self.path(rel)
        if path.stat().st_size > MAX_EDITOR_BYTES:
            raise WorkspaceError('File exceeds the 1 MiB editor limit')
        data = path.read_bytes()
        if len(data) > MAX_EDITOR_BYTES or b'\x00' in data:
            raise WorkspaceError('Binary/oversize source file not supported')
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise WorkspaceError('Source must use UTF-8') from exc
        return Document(rel, text, _sha(data))

    def save(self, rel: str, text: str, expected_sha: str | None) -> Document:
        path = self.path(rel, create=True)
        if not isinstance(text, str) or '\x00' in text:
            raise WorkspaceError('Expected UTF-8 source text')
        data = text.encode('utf-8')
        if len(data) > MAX_EDITOR_BYTES:
            raise WorkspaceError('Source exceeds 1 MiB')
        if path.exists():
            if expected_sha is None or _sha(path.read_bytes()) != expected_sha:
                raise WorkspaceError('File changed on disk; reopen before overwriting')
        elif expected_sha is not None:
            raise WorkspaceError('File removed externally; refusing to recreate')
        fd, temp_name = tempfile.mkstemp(prefix='.qeapp-write-', dir=path.parent)
        tmp = Path(temp_name)
        try:
            if path.exists():
                os.fchmod(fd, stat.S_IMODE(path.stat().st_mode)) if hasattr(os, 'fchmod') else None
            with os.fdopen(fd, 'wb') as f:
                fd = -1
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            # Recheck before replace; no system-level concurrent writer lock.
            if path.exists() and _sha(path.read_bytes()) != expected_sha:
                raise WorkspaceError('File changed while saving; retry after review')
            if not path.exists() and expected_sha is not None:
                raise WorkspaceError('File removed while saving')
            os.replace(tmp, path)
        finally:
            if fd >= 0:
                os.close(fd)
            tmp.unlink(missing_ok=True)
        return Document(rel, text, _sha(data))

    def iter_files(self, *, depth: int = 6, maximum: int = 1200) -> list[str]:
        found: list[str] = []
        def visit(folder: Path, level: int) -> None:
            if level > depth or len(found) >= maximum:
                return
            for p in sorted(folder.iterdir(), key=lambda x: x.name.casefold()):
                if p.is_symlink() or p.name.startswith('.') or p.name.casefold() in FORBIDDEN_NAMES:
                    continue
                if p.is_dir():
                    visit(p, level + 1)
                elif p.is_file() and p.suffix.casefold() in ALLOWED_EXTENSIONS | {'.png'}:
                    rel = p.relative_to(self.root).as_posix()
                    # Filtering and an editor path read use the same policy.
                    try:
                        if p.suffix.casefold() == '.png':
                            self.read_png_preview(rel)
                        else:
                            self.path(rel)
                    except WorkspaceError:
                        continue
                    found.append(rel)
                    if len(found) >= maximum:
                        return
        visit(self.root, 0)
        return found
