"""Cross-platform cancellable single process-tree runner with secret redaction."""
from __future__ import annotations
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from collections.abc import Callable
from .commands import JobSpec

class JobBusy(RuntimeError): pass

class JobRunner:
    def __init__(self):
        self._lock = threading.RLock()
        self._proc: subprocess.Popen | None = None

    @property
    def running(self) -> bool:
        with self._lock:
            return self._proc is not None and self._proc.poll() is None

    def cancel(self) -> bool:
        with self._lock:
            proc = self._proc
            if proc is None or proc.poll() is not None:
                return False
            self._stop_tree(proc)
            return True

    @staticmethod
    def _stop_tree(proc: subprocess.Popen) -> None:
        if proc.poll() is not None:
            return
        if os.name == 'nt':
            # CREATE_NEW_PROCESS_GROUP plus taskkill handles grandchildren (compiler).
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                               capture_output=True, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                proc.kill()
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def execute(self, job: JobSpec, on_output: Callable[[str], None],
                *, cwd: Path | None = None) -> int:
        if not job.argv or not isinstance(job.argv, list) or not job.argv[0]:
            raise ValueError('Job requires argv, no shell command strings')
        with self._lock:
            if self._proc is not None:
                raise JobBusy('Only one build/simulator job may run at a time')
            environment = os.environ.copy()
            environment['PYTHONUTF8'] = '1'
            proc = subprocess.Popen(job.argv, cwd=cwd, env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', bufsize=1,
                start_new_session=os.name != 'nt',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0)
            self._proc = proc
        timed_out = threading.Event()
        def timeout_kill():
            timed_out.set()
            self.cancel()
        timer = threading.Timer(job.timeout, timeout_kill)
        timer.daemon = True
        timer.start()
        displayed = 0
        max_visible = 250_000
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                for secret in job.secrets:
                    if secret:
                        line = line.replace(secret, '[REDACTED]')
                if displayed < max_visible:
                    safe = line[:max_visible - displayed]
                    displayed += len(safe)
                    on_output(safe)
                elif displayed == max_visible:
                    displayed += 1
                    on_output('[Output truncated after 250k characters]\n')
            code = proc.wait()
            if timed_out.is_set():
                on_output('TIMEOUT: job exceeded its configured limit\n')
                return 124
            return code
        finally:
            timer.cancel()
            if proc.poll() is None:
                self._stop_tree(proc)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: pass
            if proc.stdout:
                proc.stdout.close()
            with self._lock:
                self._proc = None
