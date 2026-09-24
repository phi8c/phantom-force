from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from ..entities.discovered_file import DiscoveredFile


class FileDownloader(ABC):
    """Provider-neutral contract for downloading a discovered file."""

    @abstractmethod
    async def download(self, file: DiscoveredFile) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def download_stream(self, file: DiscoveredFile) -> AsyncIterator[bytes]:
        raise NotImplementedError
