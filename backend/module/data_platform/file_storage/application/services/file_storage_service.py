from module.data_platform.file_storage.domain.contracts.file_storage import (
    FileStorage,
)
from collections.abc import AsyncIterator


class FileStorageService:

    def __init__(
        self,
        storage: FileStorage,
    ) -> None:
        self._storage = storage

    async def upload(
        self,
        path: str,
        content: bytes,
        content_type: str | None = None,
    ) -> str:

        return await self._storage.upload(
            path=path,
            content=content,
            content_type=content_type,
        )

    async def download(
        self,
        path: str,
    ) -> bytes:

        return await self._storage.download(
            path=path,
        )

    async def delete(
        self,
        path: str,
    ) -> None:

        await self._storage.delete(
            path=path,
        )
        
    async def upload_stream(
        self,
        path: str,
        content: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> str:

        return await self._storage.upload_stream(
            path=path,
            content=content,
            content_type=content_type,
        )