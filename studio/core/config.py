"""Small user-level UI configuration. Signing credentials are NEVER persisted."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile

class StudioConfig:
    ALLOWED = ('recent_projects', 'firmware_root', 'last_open_folder')

    def __init__(self, file: Path | None = None):
        if file is None:
            base = Path(os.getenv('APPDATA') or os.getenv('XDG_CONFIG_HOME') or Path.home()/'.config')
            file = base/'QEAPPStudio'/'settings.json'
        self.file = Path(file)
        self.data = {'recent_projects': [], 'firmware_root': '', 'last_open_folder': ''}
        if self.file.is_file():
            try:
                raw = json.loads(self.file.read_text(encoding='utf-8'))
                if isinstance(raw, dict):
                    for key in self.ALLOWED:
                        if key in raw and isinstance(raw[key], type(self.data[key])):
                            self.data[key] = raw[key]
            except (ValueError, UnicodeError, OSError):
                pass  # Invalid settings must not stop the editor opening.

    def update(self, **fields) -> None:
        if any(key not in self.ALLOWED for key in fields):
            raise ValueError('Unsupported preference (keys are never stored)')
        if 'recent_projects' in fields:
            items = fields['recent_projects']
            if not isinstance(items, list) or any(not isinstance(x, str) for x in items):
                raise ValueError('Recent projects must be string paths')
            fields['recent_projects'] = list(dict.fromkeys(items))[:8]
        for key in ('firmware_root', 'last_open_folder'):
            if key in fields and not isinstance(fields[key], str):
                raise ValueError('Expected path string')
        self.data.update(fields)
        self.file.parent.mkdir(parents=True, exist_ok=True)
        handle, tmp_name = tempfile.mkstemp(prefix='.settings-', suffix='.json', dir=self.file.parent)
        try:
            with os.fdopen(handle, 'w', encoding='utf-8') as fd:
                fd.write(json.dumps(self.data, indent=2, ensure_ascii=False) + '\n')
                fd.flush()
                os.fsync(fd.fileno())
            os.replace(tmp_name, self.file)
        finally:
            Path(tmp_name).unlink(missing_ok=True)

    def remember(self, project: Path) -> None:
        real = str(Path(project).resolve())
        self.update(recent_projects=[real] + [p for p in self.data['recent_projects'] if p != real])
