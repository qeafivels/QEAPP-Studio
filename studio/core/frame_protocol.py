"""Bounded IPC frame decoder shared by GUI and headless regression tests.

Wire protocol of qe_lua_host --interactive (PC only):
  b'QEFRAME <seq>\n' followed by exactly 240*270*2 RGB565-LE bytes.
No opportunistic stdout text is accepted. Partial reads are buffered until complete.
"""
from __future__ import annotations

from dataclasses import dataclass

WIDTH, HEIGHT = 240, 270
PIXEL_BYTES = WIDTH * HEIGHT * 2
HEADER_LIMIT = 40
MAX_BUFFER = PIXEL_BYTES * 3 + HEADER_LIMIT * 3

class FrameProtocolError(ValueError):
    pass

@dataclass(frozen=True)
class Frame:
    sequence: int
    rgb565_le: bytes

class FrameDecoder:
    def __init__(self):
        self._buffer = bytearray()
        self._need = None
        self._seq = None
        self._last_seq = -1

    def clear(self):
        self._buffer.clear()
        self._need = None
        self._seq = None
        self._last_seq = -1

    def feed(self, data: bytes) -> list[Frame]:
        if not isinstance(data, bytes):
            raise FrameProtocolError('Frame feed must be bytes')
        self._buffer.extend(data)
        if len(self._buffer) > MAX_BUFFER:
            raise FrameProtocolError('Host renderer output buffer overflow')
        ready: list[Frame] = []
        while True:
            if self._need is None:
                newline = self._buffer.find(b'\n')
                if newline < 0:
                    if len(self._buffer) > HEADER_LIMIT:
                        raise FrameProtocolError('Oversized frame header')
                    break
                if newline > HEADER_LIMIT:
                    raise FrameProtocolError('Oversized frame header')
                raw = bytes(self._buffer[:newline])
                del self._buffer[:newline + 1]
                if not raw.startswith(b'QEFRAME '):
                    raise FrameProtocolError('Unrecognized host renderer header')
                num = raw[len(b'QEFRAME '):]
                if not num or len(num) > 10 or any(c not in b'0123456789' for c in num):
                    raise FrameProtocolError('Invalid frame sequence number')
                seq = int(num)
                if seq != self._last_seq + 1:
                    raise FrameProtocolError('Dropped/reordered host frame sequence')
                self._seq = seq
                self._need = PIXEL_BYTES
            if len(self._buffer) < self._need:
                break
            payload = bytes(self._buffer[:self._need])
            del self._buffer[:self._need]
            ready.append(Frame(self._seq, payload))
            self._last_seq = self._seq
            self._need = None
            self._seq = None
        return ready


def rgb565_to_rgb888(payload: bytes) -> bytes:
    """Portable integer conversion, deterministic, used in tests/optional exporter.

    GUI uses QImage.Format_RGB16 directly to avoid an intermediate RGB888 copy.
    """
    if len(payload) != PIXEL_BYTES:
        raise FrameProtocolError('RGB565 frame has invalid length')
    output = bytearray(WIDTH * HEIGHT * 3)
    for i in range(0, len(payload), 2):
        color = payload[i] | (payload[i + 1] << 8)
        k = i // 2 * 3
        output[k] = ((color >> 11) & 0x1f) * 255 // 31
        output[k+1] = ((color >> 5) & 0x3f) * 255 // 63
        output[k+2] = (color & 0x1f) * 255 // 31
    return bytes(output)
