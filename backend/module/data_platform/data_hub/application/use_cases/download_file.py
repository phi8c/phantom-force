from __future__ import annotations

from ...domain.contracts.file_downloader import FileDownloader
from ...domain.entities.discovered_file import DiscoveredFile


class DownloadFileUseCase:
    def __init__(
        self,
        file_downloader: FileDownloader,
    ) -> None:
        self._file_downloader = file_downloader

    async def execute(
        self,
        file: DiscoveredFile,
    ) -> bytes:
        return await self._file_downloader.download(file)