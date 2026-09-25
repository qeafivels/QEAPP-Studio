"""v0.7 searchable workspace and diagnostic protocol regression (no Qt)."""
from pathlib import Path
import tempfile
import unittest
from studio.core.workspace import Workspace
from studio.core.project_search import search_project, MAX_RESULTS
from studio.core.host_metrics import parse_metric

class WorkbenchCoreTests(unittest.TestCase):
    def test_search_and_dirty_editor_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'qeapp.project.json').write_text('{}',encoding='utf-8')
            (root/'main.lua').write_text('local Apple = 1\nprint(Apple)\n', encoding='utf-8')
            (root/'notes.txt').write_text('apple\n', encoding='utf-8')
            w = Workspace(root)
            result = search_project(w, 'Apple')
            self.assertEqual([(m.path, m.line, m.column) for m in result.matches],
                             [('main.lua',1,7),('main.lua',2,7),('notes.txt',1,1)])
            dirty = search_project(w,'banana', snapshots={'main.lua':'banana\n'})
            self.assertEqual([(x.path,x.line) for x in dirty.matches],[('main.lua',1)])
            self.assertEqual((root/'main.lua').read_text(), 'local Apple = 1\nprint(Apple)\n')
    def test_restrict_traversal_binary_and_results(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root/'qeapp.project.json').write_text('{}',encoding='utf-8'); (root/'main.lua').write_text('a '*700,encoding='utf-8')
            (root/'app.pem').write_text('a',encoding='utf-8')
            (root/'photo.png').write_bytes(b'a')
            (root/'.git').mkdir(); (root/'.git'/'secret.lua').write_text('a')
            (root/'build').mkdir(); (root/'build'/'secret.lua').write_text('a')
            with tempfile.TemporaryDirectory() as outer:
                try: (root/'outside.lua').symlink_to(Path(outer)/'outside.lua')
                except (OSError, NotImplementedError): pass
                result = search_project(Workspace(root), 'a', max_results=11)
                self.assertEqual(len(result.matches),11)
                self.assertTrue(result.truncated)
                self.assertEqual({r.path for r in result.matches},{'main.lua'})
            for invalid in ('', '\n', 'x'*101):
                with self.assertRaises(ValueError):search_project(Workspace(root),invalid)
            with self.assertRaises(ValueError):search_project(Workspace(root),'a',max_results=MAX_RESULTS+1)
    def test_host_metric_parsing(self):
        x=parse_metric('QEHOST_METRIC frame=30 heap_used=3232 heap_peak=4096 render_us=812')
        self.assertEqual((x.frame,x.render_us,x.peak_bytes),(30,812,4096))
        self.assertIsNone(parse_metric('QEHOST_METRIC frame=30 heap_used=4444 heap_peak=2222'))
        self.assertIsNone(parse_metric('QEHOST_METRIC frame=30 heap_used=10 heap_peak=20 render_us=9999999999999'))
        self.assertIsNone(parse_metric('not metric'))

if __name__=='__main__': unittest.main()
