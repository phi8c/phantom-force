from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .discovered_file import DiscoveredFile


@dataclass
class DiscoveryPage:
    items: list[DiscoveredFile]
    next_cursor: dict[str, Any] | None
    has_more: bool