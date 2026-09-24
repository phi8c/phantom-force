from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DataHubBrowseNode:
    id: str
    name: str
    type: str
    has_children: bool
    provider: str
    locator: Mapping[str, Any]
