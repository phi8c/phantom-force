from __future__ import annotations

from ...domain.contracts.file_downloader import FileDownloader
from ...domain.entities.discovered_file import DiscoveredFile
from collections.abc import AsyncIterator


class DownloadFileUseCase:
    def __init__(
        self,
        file_downloader: FileDownloader,
    ) -> None:
        self._file_downloader = file_downloader

    async def execute(
        self,
        file: DiscoveredFile,
    ) -> AsyncIterator[bytes]:

        async for chunk in self._file_downloader.download_stream(
            file
        ):
            yield chunk