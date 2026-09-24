from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DropboxBrowseNode:
    id: str
    name: str
    type: str
    path_lower: str | None
    path_display: str | None
    parent_path: str
    has_children: bool
