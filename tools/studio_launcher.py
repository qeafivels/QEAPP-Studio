#!/usr/bin/env python3
"""QEAPP Studio Windows launcher v0.7.4: validated GUI and safe venv slots.

Stdlib only. The Lua C source is never downloaded implicitly: request --setup-lua
explicitly and bootstrap_lua.py performs the upstream SHA256 verification.
No firmware flashing and no signature verification is skipped by this launcher.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import time
from importlib import metadata
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from typing import Callable, Sequence

if __package__:
    from .safe_runtime_update import (atomic_pointer, cleanup_failed_stage, load_pointer,
                                      new_slot, runtime_directory, update_lock, UpdateLocked)
else:
    from safe_runtime_update import (atomic_pointer, cleanup_failed_stage, load_pointer,
                                     new_slot, runtime_directory, update_lock, UpdateLocked)

ROOT = Path(__file__).resolve().parents[1]
LOGFILE = ROOT / "logs" / "launcher.log"
REQUIREMENTS = ROOT / "requirements-studio.txt"
UPDATE_STATE = ROOT / "logs" / "dependency-update-state.json"
AUTO_UPDATE_INTERVAL_S = 24 * 60 * 60
AUTO_UPDATE_RETRY_S = 6 * 60 * 60
VENV = ROOT / ".venv"
# The constraints are kept in sync with requirements-studio.txt.
DEPENDENCIES = (("PySide6", "PySide6", (6, 6), (7, 0)),
                ("cryptography", "cryptography", (41,), None),
                ("Pillow", "PIL", (10,), None))


class LaunchError(RuntimeError):
    pass


@dataclass
class Options:
    no_install: bool = False
    check_only: bool = False
    system: bool = False
    repair: bool = False
    setup_lua: bool = False
    build_vm: bool = False
    require_vm: bool = False
    diagnose: bool = False
    reinstall_deps: bool = False
    update_now: bool = False
    no_update: bool = False
    offline: bool = False
    gui_check: bool = False
    rollback_update: bool = False


class Reporter:
    def __init__(self, path: Path = LOGFILE):
        self.path = path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_file() and path.stat().st_size > 1_000_000:
                path.replace(path.with_suffix(".previous.log"))
        except OSError as exc:
            print(f"[WARN] Cannot rotate launcher log: {exc}", flush=True)

    def say(self, kind: str, message: str):
        line = f"[{kind}] {message}"
        print(line, flush=True)
        try:
            with self.path.open("a", encoding="utf-8") as log:
                log.write(datetime.now().isoformat(timespec="seconds") + " " + line + "\n")
        except OSError:
            pass  # Logging failures must not prevent the graphical IDE.


def version_tuple(text: str) -> tuple[int, ...]:
    """Parse numeric release prefix without requiring the packaging library."""
    import re
    m = re.match(r"^\s*(\d+(?:\.\d+)*)", text)
    return tuple(int(v) for v in m.group(1).split(".")) if m else ()


def missing_dependencies(version_reader: Callable[[str], str] = metadata.version) -> list[str]:
    errors = []
    for package, _module, minimum, maximum in DEPENDENCIES:
        try:
            installed = version_reader(package)
        except metadata.PackageNotFoundError:
            errors.append(f"{package}: not installed")
            continue
        except Exception as exc:
            errors.append(f"{package}: metadata error ({exc})")
            continue
        parsed = version_tuple(installed)
        if not parsed or parsed < minimum or (maximum and parsed >= maximum):
            bound = f">={'.'.join(map(str, minimum))}"
            if maximum:
                bound += f",<{'.'.join(map(str, maximum))}"
            errors.append(f"{package}: {installed}, required {bound}")
    return errors


def run(command: Sequence[str | Path], reporter: Reporter, *, timeout: int = 180,
        env: dict[str, str] | None = None, tail: int = 45) -> int:
    """No shell invocation and no user-selected secret is logged."""
    command = [str(c) for c in command]
    reporter.say("RUN", " ".join(Path(c).name if i == 0 else c for i, c in enumerate(command))
                 if not any("key" in c.lower() for c in command) else "redacted command")
    try:
        p = subprocess.run(command, cwd=ROOT, env=env, text=True,
                           encoding="utf-8", errors="replace", stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        reporter.say("ERROR", f"Command timed out ({Path(command[0]).name}).")
        return 124
    except OSError as exc:
        reporter.say("ERROR", f"Unable to start {Path(command[0]).name}: {exc}")
        return 127
    if p.stdout:
        lines = p.stdout.splitlines()
        for line in lines[-tail:]:
            reporter.say("OUTPUT", line[:600])
        if len(lines) > tail:
            reporter.say("INFO", f"Log output truncated: last {tail} lines shown.")
    reporter.say("OK" if p.returncode == 0 else "ERROR",
                 f"{Path(command[0]).name} exit code: {p.returncode}")
    return p.returncode


def python_in_venv(venv: Path | None = None) -> Path:
    venv = venv if venv is not None else VENV
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def is_venv_working(exe: Path, reporter: Reporter) -> bool:
    if not exe.is_file():
        return False
    return run([exe, "-c", "import sys; assert sys.prefix != sys.base_prefix; "
                "assert sys.version_info >= (3, 10)"], reporter, timeout=15) == 0


def ensure_python(options: Options, reporter: Reporter) -> Path:
    if sys.version_info < (3, 10):
        raise LaunchError("Python 3.10+ required. Install 64-bit Python from python.org.")
    if os.name == "nt" and struct.calcsize("P") * 8 < 64:
        raise LaunchError("64-bit Python required for supported PySide6 wheels on Windows.")
    if options.system:
        reporter.say("INFO", f"Using system Python {sys.version.split()[0]} (requested).")
        return Path(sys.executable)
    selected = python_in_venv()
    if selected.exists():
        if not is_venv_working(selected, reporter):
            if options.repair and not options.check_only:
                from datetime import timezone
                suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                backup = VENV.with_name('.venv.broken-' + suffix)
                # A repair is opt-in: retain all old files, do not delete venv.
                VENV.rename(backup)
                reporter.say('WARN', f'Broken venv backed up as {backup.name}; creating clean .venv')
                return ensure_python(Options(no_install=options.no_install, system=False), reporter)
            raise LaunchError("Existing .venv appears broken or too old. Rename it, "
                              "or explicitly run --repair (no project files are touched).")
        reporter.say("OK", "Existing project .venv is ready.")
        return selected
    if VENV.exists():
        if options.repair and not options.check_only:
            from datetime import timezone
            suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = VENV.with_name('.venv.broken-' + suffix)
            VENV.rename(backup)
            reporter.say('WARN', f'Incomplete .venv backed up as {backup.name}')
            return ensure_python(Options(no_install=options.no_install), reporter)
        raise LaunchError("An incomplete .venv exists. Use --repair to back it up, "
                          "or Rename it manually before trying again.")
    if options.check_only:
        raise LaunchError("No .venv found. Run run_studio.bat to create one, or "
                          "run_studio.bat --system --check-only to check system Python.")
    reporter.say("INFO", f"Creating isolated .venv using Python {sys.version.split()[0]}.")
    if run([sys.executable, "-m", "venv", str(VENV)], reporter, timeout=100) != 0:
        raise LaunchError("Cannot create virtual environment. Check Python ensurepip "
                          "and folder write permissions.")
    if not is_venv_working(selected, reporter):
        raise LaunchError(".venv was created but Python failed its startup check.")
    return selected


def scan_environment(reporter: Reporter, *, require_vm: bool) -> bool:
    firmware = ROOT / "firmware" / "VQEAF-OS"
    lua_src = firmware / "lib" / "VqeafLua54" / "src" / "lua.h"
    gcc, gxx = shutil.which("gcc"), shutil.which("g++")
    runner = ROOT / "build" / ("qe_lua_host.exe" if os.name == "nt" else "qe_lua_host")
    reporter.say("OK" if lua_src.exists() else "WARN",
                 "Verified Lua source is installed (header present)." if lua_src.exists()
                 else "Lua source missing. VM setup: run_studio.bat --setup-lua")
    reporter.say("OK" if gcc and gxx else "WARN",
                 "Host C/C++ compilers found." if gcc and gxx else
                 "Host VM compiler not found (gcc and g++ required, e.g. MSYS2 MinGW-w64).")
    reporter.say("OK" if runner.is_file() else "WARN",
                 "Host VM binary present." if runner.is_file() else
                 "Host VM binary missing: GUI will still run but live Lua preview needs setup.")
    if not require_vm:
        return True
    return lua_src.exists() and runner.is_file()


def setup_vm(python: Path, options: Options, reporter: Reporter):
    firmware = ROOT / "firmware" / "VQEAF-OS"
    lua_src = firmware / "lib" / "VqeafLua54" / "src" / "lua.h"
    runner = ROOT / "build" / ("qe_lua_host.exe" if os.name == "nt" else "qe_lua_host")
    if options.setup_lua and not lua_src.exists():
        if options.check_only:
            reporter.say("WARN", "--setup-lua ignored by --check-only.")
        elif run([python, "tools/bootstrap_lua.py"], reporter, timeout=150) != 0:
            reporter.say("WARN", "Lua bootstrap failed; GUI can still start.")
    if not lua_src.is_file():
        return
    if not shutil.which("gcc") or not shutil.which("g++"):
        return
    inputs = [ROOT / "runtime/src/QeLuaRuntime.cpp", ROOT / "runtime/host/qe_lua_host.cpp", lua_src]
    rebuild = options.build_vm or not runner.is_file() or (
        runner.is_file() and any(f.is_file() and f.stat().st_mtime > runner.stat().st_mtime
                                 for f in inputs))
    if rebuild and not options.check_only:
        if run([python, "tools/build_lua_host.py", "--output", str(runner)],
               reporter, timeout=240) != 0:
            reporter.say("WARN", "Host VM build failed. See diagnostics above; GUI remains usable.")


def gui_smoke(python: Path, reporter: Reporter) -> bool:
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    # Some unrelated Python packages export a conflicting third-party Qt plugin path.
    env.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
    env.pop("QT_PLUGIN_PATH", None)
    code = ("from PySide6.QtWidgets import QApplication; "
            "from cryptography.hazmat.primitives.asymmetric import ec; "
            "from PIL import Image; "
            "a=QApplication([]); assert a.platformName() == 'offscreen'; "
            "assert Image.new('RGB', (1, 1)).size == (1, 1); "
            "assert ec.SECP256R1().name == 'secp256r1'; a.quit()")
    return run([python, "-c", code], reporter, env=env, timeout=25) == 0


def _probe_versions(python: Path, reporter: Reporter) -> bool:
    """Always inspect local installed package versions, without contacting the network."""
    probe = ("from pathlib import Path; import sys; "
             "sys.path.insert(0,str(Path('tools').resolve())); "
             "from studio_launcher import missing_dependencies; "
             "issues=missing_dependencies(); "
             "print('\\n'.join(issues) if issues else 'All required versions installed'); "
             "sys.exit(bool(issues))")
    return run([python, "-c", probe], reporter, timeout=30) == 0


def _pip_check(python: Path, reporter: Reporter) -> bool:
    """Detect inconsistent dependencies even if direct top-level versions look valid."""
    return run([python, "-m", "pip", "check"], reporter, timeout=35) == 0


def _update_key(python: Path) -> dict[str, str]:
    try:
        digest = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    except OSError:
        digest = "missing"
    return {"python": str(python.resolve()), "requirements_sha256": digest}


def load_update_state(state_path: Path | None = None) -> dict:
    state_path = UPDATE_STATE if state_path is None else state_path
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def save_update_state(state: dict, reporter: Reporter, state_path: Path | None = None) -> None:
    """Updates are metadata only: never overwrite source, project files or user settings."""
    state_path = UPDATE_STATE if state_path is None else state_path
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        staged = state_path.with_suffix(".pending.json")
        staged.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(staged, state_path)
    except OSError as exc:
        reporter.say("WARN", f"Could not persist dependency update schedule: {exc}")


def auto_update_due(python: Path, options: Options, *, now: float | None = None,
                    state: dict | None = None) -> tuple[bool, str]:
    """Check local packages every launch; query pip index at most daily by default."""
    if options.check_only or options.diagnose or options.no_update or options.offline or options.no_install:
        return False, "update disabled by read-only/offline/no-update option"
    if options.system and not options.update_now:
        return False, "system Python is not upgraded implicitly (use --update-now)"
    if options.update_now or options.reinstall_deps:
        return True, "explicit update requested"
    now = time.time() if now is None else now
    state = load_update_state() if state is None else state
    if any(state.get(k) != v for k, v in _update_key(python).items()):
        return True, "new environment or requirements changed"
    success = state.get("last_success_epoch", 0)
    attempt = state.get("last_attempt_epoch", 0)
    if isinstance(attempt, (int, float)) and isinstance(success, (int, float)):
        # A failed network check should not freeze GUI startup on every launch.
        if attempt > success and 0 <= now - attempt < AUTO_UPDATE_RETRY_S:
            return False, "recent network/update failure; retry later"
        if 0 <= now - success < AUTO_UPDATE_INTERVAL_S:
            return False, "compatible dependencies checked recently (<24 h)"
    return True, "daily dependency update check due"


def _pip_install(python: Path, reporter: Reporter, *, upgrade: bool, force: bool = False) -> int:
    # Avoid interactive prompts, long network stalls, and heavy source builds on Windows.
    # pip itself verifies TLS/wheel metadata; no untrusted script is run by the batch file.
    env = dict(os.environ)
    env.update({"PIP_NO_INPUT": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_DEFAULT_TIMEOUT": "10", "PIP_RETRIES": "1"})
    command = [python, "-m", "pip", "install", "--disable-pip-version-check", "--only-binary=:all:"]
    if upgrade:
        command.append("--upgrade")
    if force:
        command.append("--force-reinstall")
    command.extend(["-r", REQUIREMENTS])
    return run(command, reporter, env=env, timeout=300, tail=80)


def ensure_pip(python: Path, options: Options, reporter: Reporter) -> None:
    """Repair a venv lacking pip using the base Python's bundled ensurepip."""
    if run([python, "-m", "pip", "--version"], reporter, timeout=25) == 0:
        return
    if options.offline or options.no_install or options.check_only:
        raise LaunchError("Selected interpreter has no working pip. Run without "
                          "--offline/--no-install/--check-only to restore bundled pip.")
    reporter.say("WARN", "pip missing/broken; attempting Python's bundled ensurepip first.")
    if run([python, "-m", "ensurepip", "--upgrade"], reporter, timeout=90) != 0:
        raise LaunchError("ensurepip failed; repair your Python installation or "
                          "recreate the project .venv using --repair.")
    if run([python, "-m", "pip", "--version"], reporter, timeout=25) != 0:
        raise LaunchError("pip still unavailable after ensurepip. See logs/launcher.log.")


def preflight(python: Path, options: Options, reporter: Reporter) -> None:
    reporter.say("INFO", "Checking local Python and pip environment...")
    ensure_pip(python, options, reporter)
    reporter.say("INFO", "Checking local Python libraries and dependency consistency...")
    installed = _probe_versions(python, reporter)
    consistent = _pip_check(python, reporter) if installed else False
    needs_install = not installed or not consistent or options.reinstall_deps
    attempted_update = False

    if needs_install:
        if options.check_only or options.no_install or options.offline:
            raise LaunchError("Missing/inconsistent GUI libraries. Start without --offline/"
                              "--no-install/--check-only to auto-install into .venv, "
                              "or install them from requirements-studio.txt.")
        reporter.say("INFO", "Installing/repairing libraries in selected Python environment...")
        if _pip_install(python, reporter, upgrade=True, force=options.reinstall_deps) != 0:
            raise LaunchError("Auto-install failed. Check internet/certificates and logs/launcher.log. "
                              "If pip partially changed packages, run --repair --reinstall-deps.")
        if not _probe_versions(python, reporter) or not _pip_check(python, reporter):
            raise LaunchError("Some dependencies are still missing/inconsistent after pip install. "
                              "Inspect logs/launcher.log.")
        attempted_update = True
    else:
        due, reason = auto_update_due(python, options)
        if due:
            reporter.say("INFO", "Automatic compatible dependency updates: " + reason)
            state = {**_update_key(python), **load_update_state()}
            # Always keep the key tied to the *current* Python/requirements file.
            state.update(_update_key(python))
            state["last_attempt_epoch"] = time.time()
            save_update_state(state, reporter)
            if _pip_install(python, reporter, upgrade=True) == 0:
                if _probe_versions(python, reporter) and _pip_check(python, reporter):
                    attempted_update = True
                else:
                    raise LaunchError("Dependency update finished but consistency verification "
                                      "failed. Review logs and run --repair --reinstall-deps.")
            else:
                reporter.say("WARN", "Update index/network failed; checking existing libraries "
                             "and continuing if GUI checks remain healthy. Retry after 6 hours "
                             "or use --update-now.")
        else:
            reporter.say("INFO", "Skipping online upgrade: " + reason)

    if not _probe_versions(python, reporter) or not _pip_check(python, reporter):
        raise LaunchError("Local dependencies are not healthy. Run --repair --reinstall-deps.")
    if not gui_smoke(python, reporter):
        raise LaunchError("Qt GUI startup probe failed. Inspect logs/launcher.log. "
                          "Try --repair --reinstall-deps (Windows Visual C++ runtime may be needed).")
    reporter.say("OK", "PySide6 offscreen, Pillow, cryptography and dependency integrity PASS.")
    if attempted_update:
        now = time.time()
        state = {**_update_key(python), "last_attempt_epoch": now, "last_success_epoch": now}
        save_update_state(state, reporter)



def post_update_gui_check(python: Path, reporter: Reporter, *, screenshot: bool = False,
                          label: str = 'active') -> bool:
    """Construct/paint the actual IDE in an isolated offscreen child process.

    Exit 0 is the only success signal. JSON and optional screenshot are emitted
    by the child and never inferred from a static import or an illustrative image.
    """
    safe_label = ''.join(c for c in label if c.isalnum() or c in '-_')[:64]
    report = ROOT / 'logs' / ('gui-check-' + safe_label + '.json')
    image = ROOT / 'logs' / ('gui-check-' + safe_label + '.png')
    env = dict(os.environ)
    env['QT_QPA_PLATFORM'] = 'offscreen'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env.pop('QT_QPA_PLATFORM_PLUGIN_PATH', None)
    env.pop('QT_PLUGIN_PATH', None)
    command = [python, '-B', 'tools/gui_post_update_check.py', '--output', report]
    if screenshot:
        command.extend(['--screenshot', image])
    code = run(command, reporter, timeout=55, env=env, tail=20)
    # Offscreen verifies the real widget tree and paint. On Windows also require
    # the actual Windows QPA platform plugin to initialize without a visible GUI.
    # This catches packages whose offscreen DLL works but qwindows.dll is broken.
    if code == 0 and os.name == 'nt':
        native_env = dict(env)
        native_env.pop('QT_QPA_PLATFORM', None)
        native_script = ('from PySide6.QtWidgets import QApplication; '
                         'a=QApplication([]); '
                         "assert a.platformName().lower() == 'windows', a.platformName(); "
                         'a.quit()')
        code = run([python, '-B', '-c', native_script], reporter, timeout=22,
                   env=native_env, tail=6)
        try:
            data = json.loads(report.read_text(encoding='utf-8'))
            data['native_windows_platform'] = 'PASS' if code == 0 else 'FAIL'
            if code != 0:
                data['status'] = 'FAIL'
                data['phase'] = 'native-windows-platform'
                data['error'] = 'Qt Windows platform DLL could not initialize'
            tmp = report.with_suffix('.native-pending.json')
            tmp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
            os.replace(tmp, report)
        except (OSError, ValueError) as exc:
            reporter.say('WARN', 'Could not annotate native Qt test report: ' + str(exc))
        if code != 0:
            reporter.say('ERROR', 'Native Windows Qt platform initialization failed.')
    reporter.say('OK' if code == 0 else 'ERROR',
                 'Real Qt IDE post-update probe ' + ('PASS' if code == 0 else 'FAIL') +
                 '; results in ' + report.name)
    return code == 0


def runtime_is_healthy(python: Path, reporter: Reporter, *, screenshot: bool = False,
                       label: str = 'active') -> bool:
    """A Qt window created and rendered using this *exact* interpreter is mandatory."""
    if not is_venv_working(python, reporter):
        return False
    if not _probe_versions(python, reporter) or not _pip_check(python, reporter):
        return False
    return post_update_gui_check(python, reporter, screenshot=screenshot, label=label)


def active_runtime(reporter: Reporter) -> tuple[Path | None, str]:
    pointer = load_pointer(ROOT)
    rel = pointer.get('active', '.venv')
    try:
        directory = runtime_directory(ROOT, rel)
        python = python_in_venv(directory)
        if is_venv_working(python, reporter):
            reporter.say('INFO', 'Selected isolated runtime: ' + rel)
            return python, rel
    except (OSError, ValueError) as exc:
        reporter.say('WARN', 'Saved runtime pointer rejected: ' + str(exc))
    if rel != '.venv':
        # A manually deleted/broken slot must not prevent an intact legacy
        # venv from being used; however, broken libraries still need staging.
        base = python_in_venv(VENV)
        if is_venv_working(base, reporter):
            reporter.say('WARN', 'Activated runtime missing; trying legacy .venv.')
            return base, '.venv'
    return None, '.venv'


def safe_preflight(python: Path, active_rel: str, options: Options,
                   reporter: Reporter) -> tuple[Path, bool]:
    """Upgrade in a fresh permanent venv slot; switch pointer only after GUI PASS.

    Never install in an existing environment (unless --system was explicitly
    selected, and even there system is read-only). The previously usable
    runtime remains available for fallback and manual rollback.
    """
    reporter.say('INFO', 'Checking the active runtime, including a real Qt offscreen window...')
    healthy = (post_update_gui_check(python, reporter, screenshot=options.gui_check,
                                     label='system') and _probe_versions(python, reporter) and
               _pip_check(python, reporter)) if options.system else (
               runtime_is_healthy(python, reporter, screenshot=options.gui_check,
                                  label='active'))
    due, reason = auto_update_due(python, options)
    if options.system:
        if options.update_now or options.reinstall_deps:
            raise LaunchError('Safe update will not mutate system Python; run without --system.')
        if not healthy:
            raise LaunchError('System Python GUI is unhealthy. Use the project .venv or repair it.')
        return python, False
    if options.check_only or options.no_install or options.offline:
        if not healthy:
            raise LaunchError('Active runtime failed GUI/dependency checks; read-only/offline mode '
                              'cannot install. Retry normally with network access.')
        reporter.say('OK', 'Existing runtime healthy; read-only/offline verification completed.')
        return python, False
    if healthy and not due and not options.reinstall_deps:
        reporter.say('INFO', 'Skipping safe update: ' + reason)
        return python, False
    reason = reason if healthy else 'active runtime failed GUI/dependency validation'
    reporter.say('INFO', 'Safe update: preparing a separate environment (' + reason + ').')
    if shutil.disk_usage(ROOT).free < 650 * 1024 * 1024:
        if healthy:
            reporter.say('WARN', 'Safe update skipped: at least 650 MiB free space required.')
            return python, False
        raise LaunchError('Insufficient free disk space to create an isolated GUI runtime.')
    try:
        with update_lock(ROOT):
            return _stage_and_promote(python, active_rel, options, reporter, healthy)
    except UpdateLocked as exc:
        reporter.say('WARN', str(exc))
        if healthy:
            return python, False
        raise LaunchError(str(exc)) from exc


def _stage_and_promote(python: Path, active_rel: str, options: Options,
                       reporter: Reporter, healthy: bool) -> tuple[Path, bool]:
        # If the network is down, do not retry a failed automatic check on every
        # launch. Mark attempt for *this* active interpreter, never as success.
        now = time.time()
        pending = {**_update_key(python), 'last_attempt_epoch': now,
                   'last_success_epoch': load_update_state().get('last_success_epoch', 0)}
        save_update_state(pending, reporter)
        rel, staged_dir = new_slot(ROOT)
        staged = python_in_venv(staged_dir)
        success = False
        try:
            if run([sys.executable, '-m', 'venv', staged_dir], reporter, timeout=145) != 0:
                raise LaunchError('Unable to prepare a separate virtualenv for the safe update.')
            if not is_venv_working(staged, reporter):
                raise LaunchError('Staged runtime Python did not start.')
            ensure_pip(staged, options, reporter)
            if _pip_install(staged, reporter, upgrade=True) != 0:
                raise LaunchError('Dependency download/install failed in staging runtime.')
            if not runtime_is_healthy(staged, reporter, screenshot=True,
                                      label='stage-' + staged_dir.name):
                raise LaunchError('Staged dependencies or real Qt IDE post-update test FAILED.')
            # The previous slot is marked roll-backable only if it actually worked.
            old = active_rel if healthy else None
            atomic_pointer(ROOT, rel, old, reason='safe dependency upgrade: verified GUI')
            # Committed: preserve the newly selected slot even if the
            # best-effort update schedule write fails after activation.
            success = True
            reporter.say('OK', 'Safe update activated ' + rel +
                         '; previous working runtime retained: ' + str(old))
            done = time.time()
            try:
                save_update_state({**_update_key(staged), 'last_attempt_epoch': done,
                                   'last_success_epoch': done}, reporter)
            except Exception as exc:
                reporter.say('WARN', 'Runtime activated; schedule log failed: ' + str(exc))
            return staged, True
        except (OSError, LaunchError, ValueError) as exc:
            reporter.say('ERROR', 'Safe update FAILED: ' + str(exc))
            reporter.say('WARN', 'Active environment and projects were not changed.')
            if healthy:
                reporter.say('WARN', 'Retaining previously verified GUI runtime.')
                return python, False
            raise LaunchError('No working GUI runtime and the safe update failed; '
                              'check logs/launcher.log for details.') from exc
        finally:
            if not success:
                try:
                    cleanup_failed_stage(ROOT, rel)
                except OSError as exc:
                    reporter.say('WARN', 'Unable to clean failed staging environment: ' + str(exc))


def rollback_runtime(reporter: Reporter) -> Path:
    pointer = load_pointer(ROOT)
    previous = pointer.get('previous')
    current = pointer.get('active')
    if not previous or not current or previous == current:
        raise LaunchError('No previously verified runtime is registered for rollback.')
    try:
        python = python_in_venv(runtime_directory(ROOT, previous))
    except (OSError, ValueError) as exc:
        raise LaunchError('Invalid rollback runtime pointer.') from exc
    try:
        with update_lock(ROOT):
            if not runtime_is_healthy(python, reporter, screenshot=True, label='rollback'):
                raise LaunchError('Previous GUI runtime no longer passes safety checks; '
                                  'active environment kept unchanged.')
            # Recheck the source pointer after grabbing the writer lock.
            current_pointer = load_pointer(ROOT)
            if (current_pointer.get('active'), current_pointer.get('previous')) != (current, previous):
                raise LaunchError('Runtime changed while checking rollback; retry.')
            atomic_pointer(ROOT, previous, current, reason='manual/early-crash rollback')
    except UpdateLocked as exc:
        raise LaunchError(str(exc)) from exc
    stamp = time.time()
    save_update_state({**_update_key(python), 'last_attempt_epoch': stamp,
                       'last_success_epoch': stamp}, reporter)
    reporter.say('OK', 'Rolled back to ' + previous + '. New runtime retained for inspection.')
    return python


def launch_gui(python: Path, reporter: Reporter) -> int:
    reporter.say("INFO", "Starting QEAPP Studio GUI; close its window to exit.")
    # GUI stderr goes directly to the terminal and Python's faulthandler writes
    # a dedicated file, so native Qt errors are not hidden by a PIPE deadlock.
    crashfile = ROOT / "logs" / "gui-crash.log"
    crashfile.parent.mkdir(parents=True, exist_ok=True)
    if crashfile.is_file() and crashfile.stat().st_size > 1_000_000:
        crashfile.replace(crashfile.with_name('gui-crash.previous.log'))
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONFAULTHANDLER"] = "1"
    try:
        with crashfile.open("a", encoding="utf-8") as crash:
            with subprocess.Popen([str(python), "-u", str(ROOT / "run_studio.py")],
                                  cwd=ROOT, env=env, stdout=None, stderr=crash) as proc:
                code = proc.wait()
    except OSError as exc:
        raise LaunchError(f"Cannot start studio.main: {exc}") from exc
    reporter.say("OK" if code == 0 else "ERROR", f"GUI exit code {code}; "
                 f"crash diagnostics: logs/gui-crash.log")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-install", action="store_true", help="Do not run pip")
    parser.add_argument("--check-only", action="store_true", help="Run checks without changes or GUI")
    parser.add_argument("--system", action="store_true", help="Use existing system Python, not .venv")
    parser.add_argument("--repair", action="store_true", help="Back up invalid settings / broken venv; install missing dependencies")
    parser.add_argument("--diagnose", action="store_true", help="Read-only diagnostics; no venv, pip or Qt GUI required")
    parser.add_argument("--reinstall-deps", action="store_true", help="Explicitly force reinstall desktop Python dependencies")
    update = parser.add_mutually_exclusive_group()
    update.add_argument("--update-now", action="store_true", help="Check for compatible dependency updates immediately")
    update.add_argument("--no-update", action="store_true", help="Skip online upgrades; still install any missing dependencies")
    parser.add_argument("--offline", action="store_true", help="Never access network (requires all libraries already installed)")
    parser.add_argument("--gui-check", action="store_true", help="Check full offscreen IDE with screenshot, without installing or launching interactive GUI")
    parser.add_argument("--rollback-update", action="store_true", help="Verify and activate previous working environment; launch GUI")
    parser.add_argument("--setup-lua", action="store_true", help="Download SHA256-checked upstream Lua source")
    parser.add_argument("--build-vm", action="store_true", help="Force host Lua VM build when toolchain exists")
    parser.add_argument("--require-vm", action="store_true", help="Fail if host VM is not ready")
    args = Options(**vars(parser.parse_args(argv)))
    if args.gui_check: args.check_only = True
    log = Reporter()
    log.say("INFO", f"QEAPP Studio launcher; base Python {sys.version.split()[0]}; cwd={ROOT}")
    try:
        if not (ROOT / "run_studio.py").is_file() or not REQUIREMENTS.is_file():
            raise LaunchError("Incomplete QEAPP-Studio source; run_studio.py or requirements file missing.")
        if args.reinstall_deps and (args.no_install or args.offline or args.no_update or args.check_only):
            raise LaunchError("--reinstall-deps conflicts with --no-install/--offline/--no-update/--check-only.")
        if args.update_now and (args.offline or args.no_install or args.check_only):
            raise LaunchError("--update-now requires installation/network access; remove --offline/--no-install/--check-only.")
        if args.offline and args.setup_lua:
            raise LaunchError("--setup-lua downloads verified source and cannot run in --offline mode.")
        if args.rollback_update and (args.system or args.offline or args.update_now or args.reinstall_deps or args.check_only):
            raise LaunchError('--rollback-update cannot be combined with --system/--offline/upgrade/check-only.')
        if args.diagnose:
            selected, _ = active_runtime(log)
            python = selected or Path(sys.executable)
            result = run([python, 'tools/studio_doctor.py'], log, timeout=25)
            log.say('INFO', 'Diagnostic mode is read-only; no pip, downloads or GUI were launched.')
            return result
        if args.repair and not args.check_only:
            code = run([sys.executable, 'tools/studio_doctor.py', '--apply'], log, timeout=25)
            if code != 0:
                log.say('WARN', 'Settings doctor found issues; proceeding with runtime checks.')
        if args.rollback_update:
            python = rollback_runtime(log)
            setup_vm(python, args, log)
            if args.check_only:
                return 0
            return launch_gui(python, log)
        selected, active_rel = (None, '.venv') if args.system else active_runtime(log)
        python = selected or ensure_python(args, log)
        python, promoted = safe_preflight(python, active_rel, args, log)
        setup_vm(python, args, log)
        if not scan_environment(log, require_vm=args.require_vm):
            raise LaunchError('Host VM required but unavailable: install verified Lua source '
                              'and gcc/g++, then run with --build-vm.')
        if args.check_only:
            log.say('OK', 'Read-only full GUI verification complete. GUI not launched.')
            return 0
        started = time.monotonic()
        result = launch_gui(python, log)
        # Do not roll back after ordinary user exit or a crash much later.
        # Only a new runtime that failed at GUI startup qualifies; retry once.
        if promoted and result != 0 and time.monotonic() - started < 15:
            log.say('WARN', 'New GUI failed immediately; verifying automatic rollback...')
            try:
                old = rollback_runtime(log)
            except LaunchError as exc:
                log.say('ERROR', 'Automatic rollback unavailable: ' + str(exc))
            else:
                log.say('INFO', 'Launching the previous working environment once.')
                return launch_gui(old, log)
        return result
    except LaunchError as exc:
        log.say("ERROR", str(exc))
        return 2
    except KeyboardInterrupt:
        log.say("WARN", "Cancelled by user.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
