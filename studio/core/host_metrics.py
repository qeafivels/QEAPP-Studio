"""Strict bounded parser for optional diagnostics emitted on host stderr.

Performance statistics are PC host values. Never label them as board results.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

_METRIC = re.compile(r'^QEHOST_METRIC frame=([0-9]{1,8}) heap_used=([0-9]{1,12}) heap_peak=([0-9]{1,12})(?: render_us=([0-9]{1,12}))?$')

@dataclass(frozen=True)
class HostMetrics:
    frame: int
    heap_bytes: int
    peak_bytes: int
    render_us: int | None = None


def parse_metric(line: str) -> HostMetrics | None:
    if not isinstance(line, str) or len(line) > 160:
        return None
    match = _METRIC.fullmatch(line.strip())
    if not match:
        return None
    frame, used, peak = map(int, match.group(1, 2, 3))
    render = int(match.group(4)) if match.group(4) else None
    if peak < used or peak > 8 * 1024 * 1024 or (render is not None and render > 30_000_000):
        return None
    return HostMetrics(frame, used, peak, render)
