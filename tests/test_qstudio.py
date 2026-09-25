"""Unit and optional signer E2E tests; set QEAPP_FIRMWARE_ROOT to v2.4.2 checkout."""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qstudio',ROOT/'tools/qstudio.py')
q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

class ProjectTests(unittest.TestCase):
    def test_text_and_web(self):
        for n in ('text-notes','web-bookmark'):
            p,a=q.validate(ROOT/'projects'/n)
            self.assertIn(p['type'],('text','web'))
    def test_lua_proposal_must_fail(self):
        with self.assertRaisesRegex(q.ProjectError,'NOT_IMPLEMENTED'):
            q.validate(ROOT/'projects/snake-lua-proposal')
    def test_reject_path_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'qeapp.project.json').write_text('''{
              "project_format":1,"id":"safe","name":"Safe","version":"1.0",
              "type":"text","content":"../secret.txt"}''')
            with self.assertRaises(q.ProjectError):q.validate(p)
    def test_bad_type_and_https(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'qeapp.project.json').write_text('''{
              "project_format":1,"id":"bad","name":"Bad","version":"1.0",
              "type":"web","url":"http://example.com"}''')
            with self.assertRaises(q.ProjectError):q.validate(p)

@unittest.skipUnless(os.getenv('QEAPP_FIRMWARE_ROOT'),'Set QEAPP_FIRMWARE_ROOT to test actual firmware signer')
class SignerE2E(unittest.TestCase):
    def test_sign_verify_tamper(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        import subprocess,sys
        firmware=Path(os.environ['QEAPP_FIRMWARE_ROOT'])
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);key=ec.generate_private_key(ec.SECP256R1())
            priv=d/'fixture-private.pem';pub=d/'fixture-public.pem'
            priv.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
            pub.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo))
            for proj in ('text-notes','web-bookmark'):
                artifact=d/(proj+'.qeapp')
                cmd=[sys.executable,str(ROOT/'tools/qstudio.py'),'build',str(ROOT/'projects'/proj),
                     '--firmware-root',str(firmware),'--sign-key',str(priv),'-o',str(artifact)]
                x=subprocess.run(cmd, capture_output=True,text=True)
                self.assertEqual(x.returncode,0,x.stderr)
                info=q.inspect(artifact,pub,key_id=0x31534351)
                self.assertEqual(info['signature'],'PASS (against supplied PEM only)')
                bad=bytearray(artifact.read_bytes());bad[-1]^=1
                corrupted=d/(proj+'-bad.qeapp');corrupted.write_bytes(bad)
                with self.assertRaises(q.ProjectError):q.inspect(corrupted,pub)
                with self.assertRaises(q.ProjectError):q.inspect(artifact,pub,key_id=1)

class Scaffolder(unittest.TestCase):
    def test_init_text_web_and_no_overwrite(self):
        for kind in ('text','web'):
            with tempfile.TemporaryDirectory() as d:
                dest=Path(d)/'new_app'
                q.init_project(kind,dest,'new_app','New App')
                obj,assets=q.validate(dest)
                self.assertEqual(obj['id'],'new_app')
                self.assertEqual(obj['name'],'New App')
                with self.assertRaises(q.ProjectError):
                    q.init_project(kind,dest,'new_app','New App')

if __name__ == "__main__":
    unittest.main()
