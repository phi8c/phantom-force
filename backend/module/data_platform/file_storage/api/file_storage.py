from module.data_platform.file_storage.application.services.file_storage_service import (
    FileStorageService,
)
from collections.abc import AsyncIterator

class FileStorage:

    def __init__(
        self,
        service: FileStorageService,
    ) -> None:
        self._service = service

    async def upload(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:

        return await self._service.upload(
            path=path,
            content=content,
            content_type=content_type,
        )

    async def download(
        self,
        path: str,
    ) -> bytes:

        return await self._service.download(
            path=path,
        )

    async def delete(
        self,
        path: str,
    ) -> None:

        await self._service.delete(
            path=path,
        )
        
    async def upload_stream(
        self,
        path: str,
        content: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> str:

        return await self._service.upload_stream(
            path=path,
            content=content,
            content_type=content_type,
        )