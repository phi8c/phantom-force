from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class DropboxEntry:
    kind: str
    id: str
    name: str
    path_lower: str | None
    path_display: str | None
    size: int | None = None
    client_modified: datetime | None = None
    server_modified: datetime | None = None
    rev: str | None = None
    content_hash: str | None = None


@dataclass(frozen=True, slots=True)
class DropboxListPage:
    entries: list[DropboxEntry] = field(default_factory=list)
    cursor: str | None = None
    has_more: bool = False
