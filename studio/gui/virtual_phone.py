"""Interactive 240x320 virtual feature phone backed by the genuine host Lua VM.

This is NOT an ESP32 CPU/SD/WiFi/boot-ROM emulator. QProcess launches our
bounded QeLuaRuntime desktop executable (the runtime ported to firmware beta).
The binary RGB565 frame stream remains private to this local host subprocess.
"""
from __future__ import annotations
import time
from pathlib import Path
from collections import deque

from PySide6.QtCore import Qt, QProcess, QTimer, Signal, QDateTime
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QSizePolicy, QFileDialog, QWidget, QComboBox, QCheckBox,
)
from studio.core.frame_protocol import FrameDecoder, FrameProtocolError, WIDTH, HEIGHT
from studio.core.host_metrics import parse_metric
from studio.core.diagnostics import DebugSession, guest_error

ALLOWED_KEYS = frozenset(('up', 'down', 'left', 'right', 'start', 'option'))
KEYBOARD_KEYS = {
    Qt.Key_Up: 'up', Qt.Key_Down: 'down', Qt.Key_Left: 'left', Qt.Key_Right: 'right',
    Qt.Key_Return: 'start', Qt.Key_Enter: 'start', Qt.Key_Space: 'start',
    Qt.Key_Escape: 'option',
}

class VirtualPhone(QWidget):
    """PC-only device shell + live Lua VM stream, safe asynchronous QProcess."""
    log = Signal(str)
    launch_requested = Signal()
    state_changed = Signal(str)
    guest_problem = Signal(int, str)  # Lua source line, short message
    metric_sample = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('VirtualPhone')
        self.setFocusPolicy(Qt.StrongFocus)
        self.vm: QProcess | None = None
        self.decoder = FrameDecoder()
        self.pending = False
        self._started = 0.0
        self._frame_times: deque[float] = deque()
        self._last_frame_at = 0.0
        self._pending_source: Path | None = None
        self.frame_image: QImage | None = None
        self.last_image: QImage | None = None
        self._pressed: set[str] = set()
        self.paused = False
        self._stderr_pending = b''
        self._render_ms_samples: deque[float] = deque(maxlen=120)
        self._host_metric = None
        self._frame_count = 0
        self._exe: Path | None = None
        self.debug_session: DebugSession | None = None
        self.tick = QTimer(self)
        self.tick.setInterval(67)        # host VM preview, never hardware FPS
        self.tick.timeout.connect(self._tick)
        self.watchdog = QTimer(self)
        self.watchdog.setInterval(1200)
        self.watchdog.timeout.connect(self._check_stall)
        self._build_ui()
        self._render_placeholder()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        outer.setContentsMargins(8, 8, 8, 8)
        header = QHBoxLayout()
        title = QLabel('VQEAF VIRTUAL DEVICE')
        title.setObjectName('PanelTitle')
        self.fps = QLabel('HOST • 0 FPS')
        self.fps.setObjectName('MetricBadge')
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.fps)
        outer.addLayout(header)
        desc = QLabel('Lua 5.4 PC runtime  ·  240 × 320  ·  not hardware emulation')
        desc.setObjectName('Subtle')
        desc.setWordWrap(True)
        outer.addWidget(desc)

        bezel = QFrame()
        bezel.setObjectName('PhoneBezel')
        bezel.setFixedWidth(286)
        bezel_layout = QVBoxLayout(bezel)
        bezel_layout.setContentsMargins(14, 12, 14, 16)
        bezel_layout.setSpacing(8)
        brand = QLabel('V Q E A F     O S')
        brand.setAlignment(Qt.AlignCenter)
        brand.setObjectName('PhoneBrand')
        bezel_layout.addWidget(brand)
        self.screen = QLabel()
        self.screen.setFixedSize(240, 320)
        self.screen.setAlignment(Qt.AlignCenter)
        self.screen.setObjectName('VirtualLCD')
        self.screen.setStyleSheet('background:#102325; border:2px solid #54706d;')
        bezel_layout.addWidget(self.screen, alignment=Qt.AlignCenter)
        self.screen.setToolTip('PC Lua host render; hardware/peripheral simulation NOT included')

        matrix = QGridLayout()
        matrix.setSpacing(4)
        buttons = [
            ('MENU', 0, 0, 'menu'), ('▲', 0, 1, 'up'), ('A  BACK', 0, 2, 'back'),
            ('◀', 1, 0, 'left'), ('START', 1, 1, 'start'), ('▶', 1, 2, 'right'),
            ('OPTION', 2, 0, 'option'), ('▼', 2, 1, 'down'), ('B  DEL', 2, 2, 'unavailable'),
            ('SELECT  •  Game / T9', 3, 0, 'select'),
        ]
        for name, row, col, key in buttons:
            btn = QPushButton(name)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(31)
            btn.setObjectName('DpadButton' if key in ALLOWED_KEYS else 'SystemButton')
            if row == 3:
                matrix.addWidget(btn, row, col, 1, 3)
            else:
                matrix.addWidget(btn, row, col)
            if key == 'unavailable':
                btn.setToolTip('B/Delete is not yet bridged into the Lua beta VM; not a Back/Stop key.')
                btn.setEnabled(False)
            if key in ALLOWED_KEYS:
                btn.pressed.connect(lambda k=key: self.press(k))
                btn.released.connect(lambda k=key: self.release(k))
            elif key == 'menu' or key == 'back':
                btn.clicked.connect(self.stop)
            elif key == 'select':
                btn.clicked.connect(self._toggle_key_mode)
        bezel_layout.addLayout(matrix)
        outer.addWidget(bezel, alignment=Qt.AlignHCenter)

        actions = QHBoxLayout()
        self.run_btn = QPushButton('▶ Run')
        self.stop_btn = QPushButton('■ Stop')
        self.shot_btn = QPushButton('▣ PNG')
        self.run_btn.clicked.connect(self.launch_requested)
        self.stop_btn.clicked.connect(self.stop)
        self.shot_btn.clicked.connect(self.export_image)
        self.stop_btn.setEnabled(False)
        self.shot_btn.setEnabled(False)
        for btn in (self.run_btn, self.stop_btn, self.shot_btn):
            actions.addWidget(btn)
        outer.addLayout(actions)
        extras = QHBoxLayout()
        self.pause_btn = QPushButton('Pause')
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.step_btn = QPushButton('Step')
        self.step_btn.setEnabled(False)
        self.step_btn.clicked.connect(self.step_frame)
        self.speed = QComboBox()
        self.speed.addItems(['15 FPS cap', '30 FPS cap', '60 FPS cap'])
        self.speed.setToolTip('Requested PC host timer ceiling; real FPS depends on host speed.')
        self.speed.currentIndexChanged.connect(self._change_speed)
        for control in (self.pause_btn, self.step_btn, self.speed):
            extras.addWidget(control)
        outer.addLayout(extras)
        debug_row = QHBoxLayout()
        self.heap_cap = QComboBox()
        self.heap_cap.addItems(['96 KiB VM', '192 KiB VM', '384 KiB VM'])
        self.heap_cap.setCurrentIndex(1)
        self.heap_cap.setToolTip('Lua heap budget on PC; changing it requires a VM restart.')
        self.debug_toggle = QCheckBox('Debug session')
        self.debug_toggle.setToolTip('Log bounded input and performance counters in local logs/; never record Lua source or secrets.')
        self.restart_btn = QPushButton('Restart')
        self.restart_btn.clicked.connect(self.restart)
        self.restart_btn.setEnabled(False)
        debug_row.addWidget(self.heap_cap)
        debug_row.addWidget(self.debug_toggle)
        debug_row.addWidget(self.restart_btn)
        outer.addLayout(debug_row)
        self.metrics = QLabel('HOST: FPS 0  ·  latency —  ·  VM heap —')
        self.metrics.setWordWrap(True)
        self.metrics.setObjectName('MetricBadge')
        outer.addWidget(self.metrics)
        self.state = QLabel('READY • launch a Lua project to start')
        self.state.setWordWrap(True)
        self.state.setObjectName('Subtle')
        outer.addWidget(self.state)
        outer.addStretch(1)
        self.key_mode = 'GAME'

    def _debug_record(self, event: str, **fields):
        if self.debug_session is None:
            return
        try:
            self.debug_session.record(event, **fields)
        except OSError:
            # A full/unwritable log filesystem must never crash the running VM.
            self.log.emit('Debug log write failed; tracing disabled for this session.')
            self.debug_session.stop()
            self.debug_session = None

    def _change_speed(self, *_):
        self.tick.setInterval({0: 67, 1: 33, 2: 17}[self.speed.currentIndex()])

    def _release_all_keys(self):
        for key in tuple(self._pressed):
            self.release(key)

    def toggle_pause(self):
        if self.vm is None or self.vm.state() != QProcess.Running:
            return
        self.paused = not self.paused
        if self.paused:
            self.tick.stop()
            self._debug_record('pause')
            self._release_all_keys()
        else:
            self._debug_record('resume')
            self.tick.start()
        self.pause_btn.setText('Resume' if self.paused else 'Pause')
        self.step_btn.setEnabled(self.paused)
        self.state.setText(('PAUSED' if self.paused else 'RUNNING') +
                           ' · Lua host VM (not ESP32)')
        self.state_changed.emit('paused' if self.paused else 'running')

    def step_frame(self):
        if self.paused:
            self._debug_record('step')
            self._tick(force=True)

    def restart(self):
        """Restart an existing source in a fresh bounded VM; does not hot-reload unsafe guest memory."""
        if self._pending_source and self._exe:
            return self.start(self._pending_source, self._exe)
        return False

    def _toggle_key_mode(self):
        self.key_mode = 'T9' if self.key_mode == 'GAME' else 'GAME'
        self.log.emit('Virtual SELECT: UI input mode = ' + self.key_mode +
                      ' (T9 guest API not emulated)')

    def _render_placeholder(self):
        image = QImage(WIDTH, 320, QImage.Format_RGB32)
        image.fill(QColor('#122a27'))
        paint = QPainter(image)
        paint.setPen(QColor('#b0ec98'))
        paint.setFont(QFont('Consolas', 15, QFont.Bold))
        paint.drawText(image.rect().adjusted(0, -35, 0, 0), Qt.AlignCenter, 'VQEAF OS')
        paint.setFont(QFont('Consolas', 9))
        paint.setPen(QColor('#a6c9b7'))
        paint.drawText(image.rect().adjusted(12, 66, -12, -48),
                       Qt.AlignHCenter | Qt.TextWordWrap,
                       'HOST VIRTUAL PHONE\n\nPress Run to launch your Lua game.\n\nApp/web installer and SD/WiFi are not emulated.')
        paint.end()
        self.last_image = image
        self.screen.setPixmap(QPixmap.fromImage(image))

    def _compose(self, body: QImage) -> QImage:
        image = QImage(WIDTH, 320, QImage.Format_RGB32)
        image.fill(QColor('#163b34'))
        p = QPainter(image)
        p.setPen(QColor('#dbf7e6'))
        p.fillRect(0, 0, WIDTH, 29, QColor('#194c3a'))
        p.setFont(QFont('Consolas', 9, QFont.Bold))
        p.drawText(8, 18, 'VQEAF  •  HOST')
        p.drawText(191, 18, QDateTime.currentDateTime().toString('HH:mm'))
        p.drawImage(0, 29, body)
        p.fillRect(0, 299, WIDTH, 21, QColor('#174635'))
        p.drawText(8, 314, 'OPTION')
        p.drawText(174, 314, 'START')
        p.end()
        return image

    def start(self, script: Path, executable: Path):
        """Starts the validated local Lua host runner; never runs project as OS process."""
        self.stop(silent=True)
        script, executable = Path(script), Path(executable)
        if (not executable.is_file() or not script.is_file() or script.is_symlink() or
                script.suffix.lower() != '.lua' or not 0 < script.stat().st_size <= 65536):
            self.state.setText('Missing host runtime or invalid Lua source')
            self.log.emit('Host runtime missing or Lua source invalid; run host build first.')
            return False
        self._pending_source = script
        self._exe = executable
        self.decoder.clear()
        self._stderr_pending = b''
        self.paused = False
        self.pause_btn.setText('Pause')
        self.pause_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self._host_metric = None
        self._render_ms_samples.clear()
        self._frame_count = 0
        self._frame_times.clear()
        self._last_frame_at = time.monotonic()
        self._started = self._last_frame_at
        self.pending = False
        self.frame_image = None
        self._pressed.clear()
        if self.debug_toggle.isChecked():
            try:
                self.debug_session = DebugSession()
                self._debug_record('start', cap_kib=(96, 192, 384)[self.heap_cap.currentIndex()])
                if self.debug_session:
                    self.log.emit('VM debug session: ' + self.debug_session.path.name)
            except OSError as exc:
                self.debug_session = None
                self.log.emit('VM debug logging unavailable: ' + str(exc))
        proc = QProcess(self)
        proc.setWorkingDirectory(str(script.parent))
        proc.setProgram(str(executable))
        proc.setArguments([str(script), '--interactive', '--heap-kib', str((96,192,384)[self.heap_cap.currentIndex()])])
        proc.readyReadStandardOutput.connect(self._read_frames)
        proc.readyReadStandardError.connect(self._read_errors)
        proc.errorOccurred.connect(self._process_error)
        proc.finished.connect(self._process_finished)
        self.vm = proc
        proc.start()
        if not proc.waitForStarted(1800):
            self.state.setText('Host VM could not start')
            self.log.emit('Lua host process did not start.')
            self.vm = None
            proc.deleteLater()
            return False
        self.tick.start()
        self.watchdog.start()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        self.shot_btn.setEnabled(False)
        self.restart_btn.setEnabled(True)
        self.state.setText('RUNNING • Lua host VM (not ESP32)')
        self.state_changed.emit('running')
        self._tick()
        self.setFocus(Qt.OtherFocusReason)
        self.log.emit('Virtual phone started: ' + script.name)
        return True

    def _tick(self, force=False):
        if (self.vm is None or self.vm.state() != QProcess.Running or self.pending or
                (self.paused and not force)):
            return
        self.pending = True
        self._last_frame_at = time.monotonic()
        self.vm.write(f'TICK {self.tick.interval()}\n'.encode('ascii'))

    def _read_frames(self):
        if self.vm is None:
            return
        try:
            frames = self.decoder.feed(bytes(self.vm.readAllStandardOutput()))
        except FrameProtocolError as exc:
            self.log.emit('Host frame protocol error: '+str(exc))
            self.stop()
            return
        for item in frames:
            # QImage constructor references bytes until .copy(); avoid frame lifetime bugs.
            body = QImage(item.rgb565_le, WIDTH, HEIGHT, WIDTH*2, QImage.Format_RGB16).copy()
            self.frame_image = self._compose(body)
            self.last_image = self.frame_image
            self.screen.setPixmap(QPixmap.fromImage(self.frame_image))
            self.pending = False
            self.shot_btn.setEnabled(True)
            now = time.monotonic()
            self._frame_times.append(now)
            while self._frame_times and now - self._frame_times[0] > 1.0:
                self._frame_times.popleft()
            self._frame_count += 1
            if self._frame_count % 10 == 0:
                self._debug_record('frame', frame=self._frame_count, fps=len(self._frame_times),
                    heap=self._host_metric.heap_bytes if self._host_metric else 0)
            self._render_ms_samples.append((now-self._last_frame_at)*1000)
            fps = len(self._frame_times)
            self.fps.setText(f'HOST • {fps} FPS')
            heap = (f'{self._host_metric.heap_bytes//1024} KiB / '
                    f'{self._host_metric.peak_bytes//1024} KiB peak'
                    if self._host_metric else '—')
            guest = (f'{self._host_metric.render_us/1000:.1f} ms avg'
                     if self._host_metric and self._host_metric.render_us is not None else '—')
            sample = sum(self._render_ms_samples)/len(self._render_ms_samples)
            details = f'HOST {fps} FPS  ·  response {sample:.1f} ms  ·  guest frame {guest}  ·  heap {heap}'
            self.metrics.setText(details)
            self.metric_sample.emit(details)

    def _read_errors(self):
        if self.vm is None:
            return
        data = bytes(self.vm.readAllStandardError())
        if not data:
            return
        self._stderr_pending += data
        # Constrain partial stderr lines to 8 KiB, even on malformed guest output.
        if len(self._stderr_pending) > 8192:
            self.log.emit('Lua host: oversized diagnostics truncated')
            self._stderr_pending = b''
            return
        while b'\n' in self._stderr_pending:
            line, self._stderr_pending = self._stderr_pending.split(b'\n',1)
            text = line.decode('utf-8','replace').strip()
            if not text:
                continue
            parsed = parse_metric(text)
            if parsed:
                self._host_metric = parsed
            else:
                self.log.emit('Lua host: ' + text)
                if 'FAIL:' in text or 'Lua startup FAIL:' in text:
                    self._debug_record('vm_error')
                    position = guest_error(text)
                    if position:
                        self.guest_problem.emit(*position)
                    else:
                        self.guest_problem.emit(0, text[:250])

    def _check_stall(self):
        if self.pending and time.monotonic() - self._last_frame_at > 5.0:
            self.log.emit('Lua guest frame watchdog (>5s): stopping host VM.')
            self._debug_record('watchdog')
            self.guest_problem.emit(0, 'VM stalled for >5s (watchdog)')
            self.stop()

    def _process_error(self, code):
        self.log.emit('Lua host process error: '+str(code))

    def _process_finished(self, code, status):
        self.tick.stop()
        self.watchdog.stop()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.paused = False
        if self.vm is not None:
            self._read_errors()
            self.vm.deleteLater()
            self.vm = None
        self.pending = False
        self.state.setText(f'STOPPED • host exit {code}')
        if self.debug_session:
            self._debug_record('stop', exit_code=code)
            if self.debug_session: self.debug_session.stop()
            self.debug_session = None
        self.state_changed.emit('stopped')

    def press(self, key: str):
        if key not in ALLOWED_KEYS or self.vm is None or self.vm.state()!=QProcess.Running:
            return
        if key not in self._pressed:
            self._pressed.add(key)
            self.vm.write(f'KEY {key} 1\n'.encode('ascii'))
            self._debug_record('key', key=key, down=True)

    def release(self, key: str):
        if key not in ALLOWED_KEYS:
            return
        if key in self._pressed:
            self._pressed.discard(key)
            if self.vm is not None and self.vm.state()==QProcess.Running:
                self.vm.write(f'KEY {key} 0\n'.encode('ascii'))
                self._debug_record('key', key=key, down=False)

    def focusOutEvent(self, event):
        # Avoid stuck directional keys when clicking the source editor.
        self._release_all_keys()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if not event.isAutoRepeat() and event.key() in KEYBOARD_KEYS:
            self.press(KEYBOARD_KEYS[event.key()])
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat() and event.key() in KEYBOARD_KEYS:
            self.release(KEYBOARD_KEYS[event.key()])
            event.accept()
            return
        super().keyReleaseEvent(event)

    def export_image(self, path: Path | None = None):
        if self.last_image is None:
            return False
        if path is None:
            selected, _ = QFileDialog.getSaveFileName(self,'Export host frame',
                            'qeapp-host-240x320.png','PNG (*.png)')
            if not selected: return False
            path = Path(selected)
        if not str(path).lower().endswith('.png'):
            self.log.emit('Screenshot must be a PNG file')
            return False
        ok = self.last_image.save(str(path),'PNG')
        self.log.emit(('Saved screenshot: ' if ok else 'PNG save failed: ') + str(path))
        return ok

    def stop(self, silent=False):
        self.tick.stop()
        self.watchdog.stop()
        self._release_all_keys()
        self._pressed.clear()
        self.paused = False
        self.pause_btn.setText('Pause')
        self.pause_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.pending = False
        proc = self.vm
        self.vm = None     # ignore queued stale output/exit after process replaced
        if proc is not None:
            proc.blockSignals(True)
            if proc.state()!=QProcess.NotRunning:
                proc.write(b'QUIT\n')
                proc.closeWriteChannel()
                if not proc.waitForFinished(200):
                    proc.kill()
                    proc.waitForFinished(800)
            proc.deleteLater()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.debug_session:
            self._debug_record('stop', exit_code=0)
            if self.debug_session: self.debug_session.stop()
            self.debug_session = None
        if not silent:
            self.state.setText('STOPPED • ready')
            self.state_changed.emit('stopped')

    def closeEvent(self, event):
        self.stop(silent=True)
        super().closeEvent(event)
