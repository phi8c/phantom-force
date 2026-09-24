from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from ..entities.browse_node import DataHubBrowseNode


class InvalidBrowseLocatorError(ValueError):
    pass


class DataHubBrowser(ABC):
    @abstractmethod
    async def browse_root(self) -> list[DataHubBrowseNode]:
        raise NotImplementedError

    @abstractmethod
    async def browse_children(
        self,
        locator: Mapping[str, Any],
    ) -> list[DataHubBrowseNode]:
        raise NotImplementedError

    async def close(self) -> None:
        return None
