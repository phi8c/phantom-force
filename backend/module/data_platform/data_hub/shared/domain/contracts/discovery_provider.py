from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..entities.discovery_page import DiscoveryPage
from ..value_objects.source_reference import SourceReference


class DiscoveryProvider(ABC):
    """Provider-neutral contract for paged, resumable file discovery."""

    @abstractmethod
    async def discover(
        self,
        source: SourceReference,
        *,
        cursor: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> DiscoveryPage:
        raise NotImplementedError
