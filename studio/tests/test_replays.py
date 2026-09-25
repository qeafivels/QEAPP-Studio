"""M2 Lua replay recorder tests: parser is shared by UI and runner."""
from pathlib import Path
import json
import tempfile
import unittest
from studio.core.replays import ReplayEvent, ReplayError, canonical, parse, serialize, as_host_lines
from studio.core import commands
from studio.core.workspace import Workspace

class ReplayTests(unittest.TestCase):
    def test_round_trip_and_order_within_frame(self):
        data = [ReplayEvent(2, 'right', True), ReplayEvent(0, 'start', True),
                ReplayEvent(2, 'right', False)]
        self.assertEqual(parse(serialize(data, 8), 8),
                         [data[1],data[0],data[2]])
        self.assertEqual(as_host_lines(data, 8),
                         '0 start 1\n2 right 1\n2 right 0\n')

    def test_hard_limits_and_reserved_os_keys(self):
        for records in ([], [ReplayEvent(0,'menu',True)], [ReplayEvent(0,'select',True)],
                        [ReplayEvent(True,'up',True)], [ReplayEvent(8,'up',True)],
                        [ReplayEvent(0,'up',1)], [ReplayEvent(0,'up',True)]*129):
            with self.subTest(records=records[:2]), self.assertRaises(ReplayError):
                serialize(records, 8)

    def test_untrusted_json_rejected(self):
        bad = [b'\xff', '[{}]', '"not a list"',
               '[{"frame":0,"key":"menu","down":true}]',
               '[{"frame":true,"key":"up","down":true}]',
               '[{"frame":0,"key":"up","down":false,"extra":0}]',
               ' ' * 8200]
        for payload in bad:
            with self.subTest(payload=str(payload)[:35]), self.assertRaises(ReplayError):
                parse(payload, 8)

    def test_source_parser_runner_contract(self):
        from tools.lua_preview import prepare_replay
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            source=folder/'events.json';target=folder/'events.txt'
            source.write_text(serialize([ReplayEvent(3, 'down', False),
                                         ReplayEvent(1, 'start', True)], 8))
            self.assertEqual(prepare_replay(source,target,8), 2)
            self.assertEqual(target.read_text(), '1 start 1\n3 down 0\n')
            source.write_text('[{"frame":0,"key":"b","down":true}]')
            with self.assertRaises(ReplayError):
                prepare_replay(source,target,8)

    def test_safe_workspace_save(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d);(project/'qeapp.project.json').write_text('{}')
            workspace=Workspace(project);workspace.mkdir('tests')
            doc=workspace.save('tests/input_replay.json',
                               serialize([ReplayEvent(0,'start',True)],8),None)
            with self.assertRaisesRegex(ValueError,'changed'):
                workspace.save('tests/input_replay.json','[]',None)
            self.assertEqual(parse(workspace.read('tests/input_replay.json').text,8),
                             [ReplayEvent(0,'start',True)])
            doc2=workspace.save('tests/input_replay.json',
                      serialize([ReplayEvent(0,'up',True)],8),doc.sha256)
            self.assertNotEqual(doc.sha256,doc2.sha256)

    def test_command_frames(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d); (project/'tests').mkdir()
            (project/'tests/input_replay.json').write_text('[]')
            spec=commands.lua_preview(project,project/'out.png',32)
            self.assertIn('32', spec.argv)
            self.assertIn('--replay',spec.argv)
            for invalid in (0,201,False):
                with self.assertRaises(ValueError):
                    commands.lua_preview(project,project/'out.png',invalid)

if __name__=='__main__': unittest.main()
