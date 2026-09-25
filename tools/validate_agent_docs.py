#!/usr/bin/env python3
"""Validate QEAPP-Studio agent documentation and its SHA-256 manifest.

Checks documentation only. PASS never proves Qt, Lua host or physical board runs.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    'PROMPT.md', 'SKILLS.md', 'AGENTS.md', 'README.md', 'README_INSTALL.md',
    'DOCS_MANIFEST.json', 'CHANGELOG_AGENT_KIT_v1.1.md',
    'agents/README.md', 'agents/orchestrator.md', 'agents/studio-gui.md',
    'agents/lua-runtime.md', 'agents/app-template.md',
    'agents/package-security.md', 'agents/firmware-core.md',
    'agents/qa-release.md', 'docs/agents/README.md',
    'docs/agents/PROJECT_STRUCTURE.md', 'docs/agents/TASK_BRIEF_TEMPLATE.md',
    'docs/agents/TEST_MATRIX.md', 'docs/agents/HANDOFF_TEMPLATE.md',
    'studio/gui/window.py', 'studio/gui/virtual_phone.py',
    'studio/core/workspace.py', 'runtime/src/QeLuaRuntime.cpp',
    'tools/qstudio.py', 'tools/studio_launcher.py',
    'tools/gui_post_update_check.py', 'tools/test_agent_docs.py',
)
DOCS = [ROOT / s for s in REQUIRED if s.lower().endswith('.md')]
INLINE_LINK = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')


def validate():
    problems = []
    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            problems.append(f'Missing: {rel}')
    for doc in DOCS:
        if not doc.exists():
            continue
        content = doc.read_text(encoding='utf-8')
        if not content.strip():
            problems.append(f'Empty: {doc.relative_to(ROOT)}')
        # Limit link scanner to actual Markdown links; exclude fenced code blocks.
        plain = re.sub(r'^```.*?^```', '', content, flags=re.MULTILINE | re.DOTALL)
        for raw in INLINE_LINK.findall(plain):
            url = raw.split('#', 1)[0].strip().split(' ', 1)[0]
            if not url or url.startswith(('https://', 'http://', 'mailto:', 'sandbox:')):
                continue
            candidate = (doc.parent / url).resolve()
            if not candidate.is_relative_to(ROOT.resolve()) or not candidate.is_file():
                problems.append(f'Broken relative link: {doc.relative_to(ROOT)} -> {raw}')
    cli_path = ROOT / 'tools/qstudio.py'
    if cli_path.is_file():
        cli = cli_path.read_text('utf-8')
        for cmd in ('init', 'validate', 'doctor', 'build', 'inspect', 'test', 'lua-preview', 'simulate'):
            if f"sub.add_parser('{cmd}'" not in cli:
                problems.append(f'CLI no longer defines command: {cmd}; revise docs')
    prompt = ROOT / 'PROMPT.md'
    if prompt.is_file():
        content = prompt.read_text('utf-8')
        for token in ('GUI', 'Lua', 'Back', 'Retro-Go', 'SKIPPED', 'NOT_RUN'):
            if token not in content:
                problems.append(f'PROMPT.md missing critical term: {token}')
    matrix = ROOT / 'docs/agents/TEST_MATRIX.md'
    handoff = ROOT / 'docs/agents/HANDOFF_TEMPLATE.md'
    agents = ROOT / 'AGENTS.md'
    if all(p.is_file() for p in (matrix, handoff, agents)):
        all_content = [p.read_text('utf-8') for p in (matrix, handoff, agents)]
        for token in ('PASS', 'FAIL', 'SKIPPED', 'NOT_RUN', 'STATIC', 'HOST', 'GUI_QT', 'PIO_BUILD', 'DEVICE'):
            if not all(token in txt for txt in all_content[:2]):
                problems.append(f'Matrix/handoff missing status or tier: {token}')
        for tid in ('DOC01', 'GUI01', 'VM01', 'PKG02', 'FW02', 'DEV01', 'DEV03', 'SEC01', 'REL01'):
            if f'`{tid}`' not in all_content[0]:
                problems.append(f'Matrix missing test ID: {tid}')
    manifest_file = ROOT / 'DOCS_MANIFEST.json'
    if manifest_file.is_file():
        try:
            manifest = json.loads(manifest_file.read_text('utf-8'))
            if manifest.get('docs_version') != '1.1':
                problems.append('Expected DOCS_MANIFEST version 1.1')
            for entry in manifest['content']:
                p = (ROOT / entry['path']).resolve()
                if not p.is_relative_to(ROOT.resolve()) or not p.is_file():
                    problems.append('Missing/outside manifest path: '+entry['path'])
                elif p.stat().st_size != entry['size'] or hashlib.sha256(p.read_bytes()).hexdigest() != entry['sha256']:
                    problems.append('Manifest mismatch: '+entry['path'])
        except (KeyError, ValueError, TypeError, OSError) as exc:
            problems.append(f'Invalid DOCS_MANIFEST.json: {exc}')
    return problems


def main():
    problems = validate()
    if problems:
        print('AI documentation check: FAIL')
        for problem in problems:
            print(' -', problem)
        return 1
    print(f'AI documentation check: PASS ({len(REQUIRED)} required paths, {len(DOCS)} Markdown docs, SHA-256 manifest verified)')
    print('Scope: DOCS ONLY; GUI/VM/DEVICE not tested by this command')
    return 0


if __name__ == '__main__':
    sys.exit(main())
