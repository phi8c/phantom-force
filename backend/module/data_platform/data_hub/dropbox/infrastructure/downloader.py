from __future__ import annotations

from collections.abc import AsyncIterator

from module.data_platform.data_hub.shared.domain.contracts.file_downloader import (
    FileDownloader,
)
from module.data_platform.data_hub.shared.domain.entities.discovered_file import (
    DiscoveredFile,
)

from ..domain.contracts.client import DropboxClient


class DropboxFileDownloader(FileDownloader):
    PROVIDER_NAME = "dropbox"

    def __init__(self, client: DropboxClient, *, chunk_size: int = 64 * 1024) -> None:
        if chunk_size <= 0:
            raise ValueError("Download chunk size must be greater than 0.")
        self._client = client
        self._chunk_size = chunk_size

    async def download(self, file: DiscoveredFile) -> bytes:
        return await self._client.download(self._download_identity(file))

    async def download_stream(self, file: DiscoveredFile) -> AsyncIterator[bytes]:
        content = await self.download(file)
        for offset in range(0, len(content), self._chunk_size):
            yield content[offset : offset + self._chunk_size]

    @classmethod
    def _download_identity(cls, file: DiscoveredFile) -> str:
        if file.source.provider.strip().lower() != cls.PROVIDER_NAME:
            raise ValueError("Dropbox downloader requires a Dropbox discovered file.")

        metadata = file.provider_metadata
        for key in ("id", "path_lower", "path_display"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value
        if file.original_file_path:
            return file.original_file_path
        raise ValueError("Discovered file has no Dropbox download identity.")
