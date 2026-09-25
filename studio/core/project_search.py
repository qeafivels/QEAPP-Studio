"""Bounded, literal project-wide UTF-8 search sharing Workspace's path rules.

No regex evaluation, symlink traversal, binary reads, hidden/build/key folders,
or unbounded file scanning. Optional dirty editor snapshots take precedence over
on-disk documents without writing edits as a side effect.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping
from studio.core.workspace import Workspace, WorkspaceError

MAX_FILES = 500
MAX_BYTES = 8 * 1024 * 1024
MAX_RESULTS = 250
MAX_QUERY = 100

@dataclass(frozen=True)
class SearchMatch:
    path: str
    line: int
    column: int
    excerpt: str

@dataclass(frozen=True)
class SearchReport:
    matches: tuple[SearchMatch, ...]
    files_scanned: int
    bytes_scanned: int
    truncated: bool


def search_project(workspace: Workspace, query: str, *, snapshots: Mapping[str, str] | None = None,
                   case_sensitive: bool = False, max_results: int = MAX_RESULTS) -> SearchReport:
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY or any(
        ord(ch) < 32 for ch in query):
        raise ValueError('Search query must be 1..100 printable characters')
    if not 1 <= max_results <= MAX_RESULTS:
        raise ValueError('Invalid result limit')
    needle = query if case_sensitive else query.casefold()
    snapshots = snapshots or {}
    matches: list[SearchMatch] = []
    count = total = 0
    truncated = False
    # Workspace.iter_files applies the same allow-list and symlink rules as editor.
    listed = workspace.iter_files(maximum=1201)
    files = [path for path in listed if not path.lower().endswith('.png')]
    if len(listed) >= 1201 or len(files) > MAX_FILES:
        truncated = True
    for rel in files[:MAX_FILES]:
        try:
            if rel in snapshots:
                # Still validate the real file path; snapshots cannot smuggle paths.
                workspace.path(rel)
                if not isinstance(snapshots[rel], str) or len(snapshots[rel]) > 1024*1024:
                    continue
                data = snapshots[rel].encode('utf-8')
                if len(data) > 1024*1024 or b'\0' in data:
                    continue
                content = snapshots[rel]
            else:
                content = workspace.read(rel).text
                data = content.encode('utf-8')
        except (WorkspaceError, OSError, UnicodeError):
            continue
        if total + len(data) > MAX_BYTES:
            truncated = True
            break
        total += len(data)
        count += 1
        for number, line in enumerate(content.splitlines(), 1):
            text = line if case_sensitive else line.casefold()
            start = 0
            while True:
                found = text.find(needle, start)
                if found < 0:
                    break
                matches.append(SearchMatch(rel, number, found + 1, line[:220]))
                if len(matches) >= max_results:
                    truncated = True
                    return SearchReport(tuple(matches), count, total, truncated)
                start = found + len(needle)
    return SearchReport(tuple(matches), count, total, truncated)
