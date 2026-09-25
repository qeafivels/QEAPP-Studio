#!/usr/bin/env python3
"""Stdlib-only regression for QEAPP AI-agent document templates.

It validates existence/cross-reference and negative status semantics without
asserting anything about GUI, Lua firmware or attached hardware.
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class AgentDocsContract(unittest.TestCase):
    def test_template_locations(self):
        for name in (
            'AGENTS.md', 'agents/orchestrator.md',
            'docs/agents/TASK_BRIEF_TEMPLATE.md',
            'docs/agents/HANDOFF_TEMPLATE.md',
            'docs/agents/TEST_MATRIX.md',
        ):
            self.subTest(name=name)
            self.assertTrue((ROOT / name).is_file(), name)

    def test_status_levels(self):
        handoff = (ROOT / 'docs/agents/HANDOFF_TEMPLATE.md').read_text('utf-8')
        matrix = (ROOT / 'docs/agents/TEST_MATRIX.md').read_text('utf-8')
        for tok in ('PASS', 'FAIL', 'SKIPPED', 'NOT_RUN', 'STATIC', 'HOST', 'GUI_QT', 'PIO_BUILD', 'DEVICE'):
            with self.subTest(token=tok):
                self.assertIn(tok, handoff)
                self.assertIn(tok, matrix)

    def test_test_ids_and_firmware_visual_gate(self):
        matrix = (ROOT / 'docs/agents/TEST_MATRIX.md').read_text('utf-8')
        for tid in ('DOC01', 'GUI01', 'VM01', 'PKG02', 'FW02', 'DEV01', 'DEV03', 'SEC01', 'REL01'):
            with self.subTest(id=tid):
                self.assertIn(f'`{tid}`', matrix)
        self.assertIn('SHA-256', matrix)
        self.assertIn('Serial 115200', matrix)

    def test_manifest_consistency(self):
        manifest = json.loads((ROOT / 'DOCS_MANIFEST.json').read_text('utf-8'))
        listed = {x['path'] for x in manifest['content']}
        for required in ('AGENTS.md', 'docs/agents/HANDOFF_TEMPLATE.md', 'docs/agents/TEST_MATRIX.md'):
            self.assertIn(required, listed)

    def test_orchestrator_handoff_requirements(self):
        body = (ROOT / 'AGENTS.md').read_text('utf-8')
        for word in ('BLOCKED', 'Task Brief', 'QA_REVIEW', 'Retro-Go', 'baseline', 'NOT_RUN'):
            self.assertIn(word, body)


if __name__ == '__main__':
    unittest.main()
