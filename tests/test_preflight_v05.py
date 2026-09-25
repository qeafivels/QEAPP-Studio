"""Static readiness report is truthful about target preconditions and beta gating."""
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.device_preflight import inspect
from studio.core.commands import beta_preflight

class Preflight(unittest.TestCase):
    def test_current_source_reports_missing_external_dependencies(self):
        report=inspect(ROOT/'firmware/VQEAF-OS',source_root=ROOT)
        self.assertEqual(report['status'],'NOT_READY')
        self.assertEqual(report['checks']['runtime_mirror']['status'],'READY')
        self.assertEqual(report['checks']['beta_profile']['status'],'READY')
        self.assertEqual(report['checks']['stock_isolated']['status'],'READY')
        self.assertEqual(report['checks']['lua_source']['status'],'MISSING')
        self.assertEqual(report['checks']['beta_public_key']['status'],'MISSING')
        self.assertEqual(report['device_build'],'NOT_RUN')

    def test_hypothetical_ready_paths_still_do_not_claim_hardware_success(self):
        with tempfile.TemporaryDirectory() as d:
            fw=Path(d)/'VQEAF-OS'
            (fw/'lib/VqeafLua54/src').mkdir(parents=True)
            (fw/'src/lua').mkdir(parents=True)
            (fw/'src/services').mkdir(parents=True)
            (fw/'platformio.ini').write_text('''[env:vqeaf_os]\nbuild_flags = -D BASE\n[env:vqeaf_lua_beta]\nbuild_flags = -D VQEAF_ENABLE_LUA=1 -D QE_LUA_PSRAM_ALLOC=1 -D VQEAF_LUA_BETA_TRUST=1\n''')
            for file in ('lua.h','lua.c','lauxlib.c','lualib.h'):
                (fw/'lib/VqeafLua54/src'/file).write_text('fake source placeholder')
            (fw/'src/services/QeappTrustKeyLuaBeta.h').write_text('// only public declaration TEST\n')
            src=(ROOT/'runtime/src/QeLuaRuntime.cpp').read_text()
            (fw/'src/lua/QeLuaRuntime.cpp').write_text('#if defined(VQEAF_ENABLE_LUA) && VQEAF_ENABLE_LUA\n'+src+'\n#endif // VQEAF_ENABLE_LUA\n')
            report=inspect(fw,cli='fake-pio',source_root=ROOT)
            self.assertEqual(report['status'],'READY_FOR_DEVICE_BUILD')
            self.assertEqual(report['device_build'],'NOT_RUN')
            self.assertEqual(report['hardware_test'],'NOT_RUN')

    def test_preflight_command_is_direct_python_not_shell(self):
        spec=beta_preflight(ROOT/'firmware/VQEAF-OS')
        self.assertEqual(spec.argv[0],sys.executable)
        self.assertEqual(spec.timeout,20)
        self.assertEqual(spec.argv[2],'--firmware-root')

if __name__=='__main__':unittest.main()
