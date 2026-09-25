"""Runs only on machines with PySide6. Skip is visible (never count as PASS)."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

try:
    HAS_QT=importlib.util.find_spec('PySide6') is not None
except ValueError:
    HAS_QT=False

@unittest.skipUnless(HAS_QT, 'PySide6 not installed: GUI has NOT been run here')
class QtSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['QT_QPA_PLATFORM']='offscreen'
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_create_project_and_open_editor(self):
        from studio.gui.window import StudioWindow
        from tools.qstudio import init_project
        with tempfile.TemporaryDirectory() as d:
            project=Path(d)/'small'
            init_project('text',project,'small','Small')
            view=StudioWindow()
            view._set_project(project)
            view.open_document('content.txt')
            self.assertEqual(view.tabs.count(),1)
            self.assertIn('content.txt',view.editors)
            view.close()

    def test_editor_go_to_line_and_gutter(self):
        from studio.gui.window import CodeEditor
        from studio.core.workspace import Document
        editor=CodeEditor(Document('main.lua', 'one\ntwo\nthree\n', 'test-sha'))
        self.assertGreater(editor.gutter_width(),10)
        self.assertTrue(editor.goto(2, 3))
        self.assertEqual((editor.textCursor().blockNumber(),editor.textCursor().positionInBlock()),(1,2))
        self.assertFalse(editor.goto(900))
        editor.close()

    def test_initial_window(self):
        from studio.gui.window import StudioWindow
        view=StudioWindow()
        self.assertIn('QEAPP Studio',view.windowTitle())
        self.assertFalse(view.btn_stop.isEnabled())
        view.close()

    def test_v072_diagnostics_vm_controls_and_repair(self):
        from studio.gui.window import StudioWindow
        w=StudioWindow()
        try:
            self.assertEqual(w.device.heap_cap.currentIndex(), 1)
            self.assertEqual(w.device.speed.count(), 3)
            w.device.speed.setCurrentIndex(2)
            self.assertEqual(w.device.tick.interval(),17)
            w.show_diagnostics()
            self.assertEqual(w.right_tabs.currentWidget(),w.diag_page)
            self.assertIn('Qt image allocation',w.diag_output.toPlainText())
            w.on_guest_problem(0,'Synthetic test VM error')
            self.assertTrue(w.problems.topLevelItemCount()>=1)
        finally:w.close()

    def test_v07_virtual_device_layout(self):
        from studio.gui.window import StudioWindow
        w=StudioWindow()
        try:
            self.assertEqual(w.device.screen.width(),240)
            self.assertEqual(w.device.screen.height(),320)
            self.assertTrue(w.right_tabs.count()>=2)
            self.assertIsNone(w.device.vm)
            self.assertFalse(w.btn_stop.isEnabled())
            self.assertFalse(w.device.pause_btn.isEnabled())
            self.assertFalse(w.device.step_btn.isEnabled())
            self.assertEqual(w.left_pages.count(), 2)
            w.show_project_search()
            self.assertEqual(w.left_pages.currentIndex(), 1)
            w.device.speed.setCurrentIndex(1)
            self.assertEqual(w.device.tick.interval(), 33)
            w.device.speed.setCurrentIndex(0)
            self.assertEqual(w.device.tick.interval(), 67)
        finally:
            w.close()
