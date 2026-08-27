from __future__ import annotations

from abc import ABC, abstractmethod

from collections.abc import AsyncIterator
from ..entities.discovered_file import DiscoveredFile


class FileDownloader(ABC):
    """
    Contract for downloading a discovered file.
    """

    @abstractmethod
    async def download(
        self,
        file: DiscoveredFile,
    ) -> bytes:
        """
        Download the content represented by a discovered file.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def download_stream(
        self,
        file: DiscoveredFile,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError