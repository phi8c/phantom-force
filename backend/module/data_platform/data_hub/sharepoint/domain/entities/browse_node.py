from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrowseNode:
    id: str
    name: str
    type: str
    site_id: str | None = None
    drive_id: str | None = None
    parent_id: str | None = None
    has_children: bool = False
