"""Deterministic project-local key replay contract for Lua host previews.

This module deliberately has no Qt dependency. The same bounded parser is used by
Studio recording and the lua_preview subprocess; reserved OS keys never reach VM.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

VALID_KEYS = frozenset({'left', 'right', 'up', 'down', 'start', 'option'})
MAX_REPLAY_BYTES = 8192
MAX_EVENTS = 128
MAX_FRAMES = 200


class ReplayError(ValueError):
    pass


@dataclass(frozen=True)
class ReplayEvent:
    frame: int
    key: str
    down: bool


def _validate(event: ReplayEvent, frames: int) -> None:
    if type(frames) is not int or not 1 <= frames <= MAX_FRAMES:
        raise ReplayError('Replay frame count must be 1..200')
    if (type(event.frame) is not int or not 0 <= event.frame < frames
            or type(event.key) is not str or event.key not in VALID_KEYS
            or type(event.down) is not bool):
        raise ReplayError('Invalid replay event: reserved OS keys and out-of-range frames are forbidden')


def canonical(events: Iterable[ReplayEvent], frames: int = MAX_FRAMES) -> list[ReplayEvent]:
    normalized = list(events)
    if not 1 <= len(normalized) <= MAX_EVENTS:
        raise ReplayError('Replay must contain 1..128 key events')
    for event in normalized:
        if not isinstance(event, ReplayEvent):
            raise ReplayError('Expected ReplayEvent records')
        _validate(event, frames)
    # Stable sort preserves deliberate press/release order within a frame.
    return sorted(normalized, key=lambda event: event.frame)


def parse(raw: str | bytes, frames: int = MAX_FRAMES) -> list[ReplayEvent]:
    if isinstance(raw, bytes):
        if len(raw) > MAX_REPLAY_BYTES:
            raise ReplayError('Replay too large (max 8192 bytes)')
        try:
            raw = raw.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ReplayError('Replay must be UTF-8') from exc
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > MAX_REPLAY_BYTES:
        raise ReplayError('Replay too large (max 8192 bytes)')
    try:
        records = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise ReplayError('Invalid replay JSON') from exc
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_EVENTS:
        raise ReplayError('Replay must contain 1..128 events')
    parsed = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {'frame', 'key', 'down'}:
            raise ReplayError('Every replay event needs exactly frame, key and down')
        parsed.append(ReplayEvent(record['frame'], record['key'], record['down']))
    return canonical(parsed, frames)


def serialize(events: Iterable[ReplayEvent], frames: int = MAX_FRAMES) -> str:
    records = [{'frame': event.frame, 'key': event.key, 'down': event.down}
               for event in canonical(events, frames)]
    text = json.dumps(records, indent=2, ensure_ascii=True) + '\n'
    if len(text.encode('utf-8')) > MAX_REPLAY_BYTES:
        raise ReplayError('Replay too large (max 8192 bytes)')
    return text


def as_host_lines(events: Iterable[ReplayEvent], frames: int) -> str:
    return ''.join(f'{e.frame} {e.key} {int(e.down)}\n' for e in canonical(events, frames))
