from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Provider-neutral reference to a source or source location."""

    provider: str
    identifier: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
