"""Standalone repo separation tests; no firmware / hardware required."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from studio_firmware import firmware_root

class Standalone(unittest.TestCase):
    def test_required_error_when_path_invalid(self):
        with patch.dict(os.environ, {'QEAPP_FIRMWARE_ROOT':'/path/does/not/exist'}):
            with self.assertRaises(FileNotFoundError):firmware_root(required=True)
    def test_configured_external_firmware(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'platformio.ini').write_text('[env]')
            with patch.dict(os.environ,{'QEAPP_FIRMWARE_ROOT':str(p)}):
                self.assertEqual(firmware_root(required=True),p.resolve())
    def test_no_firmware_is_optional_for_gui(self):
        with patch.dict(os.environ,{'QEAPP_FIRMWARE_ROOT':'/path/does/not/exist'}):
            self.assertIsNone(firmware_root())
    def test_no_firmware_snapshot_embedded(self):
        self.assertFalse((ROOT/'firmware/VQEAF-OS/platformio.ini').exists())

if __name__=='__main__':unittest.main()
