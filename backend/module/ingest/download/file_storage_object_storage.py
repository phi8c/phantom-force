from collections.abc import AsyncIterator
from uuid import UUID

from module.ingest.download.domain.contracts.object_storage import (
    ObjectStorage,
    StoredObject,
)


class FileStorageObjectStorage(
    ObjectStorage,
):

    def __init__(
        self,
        file_storage,
        storage_provider_id: UUID,
    ):
        self._file_storage = file_storage
        self._storage_provider_id = (
            storage_provider_id
        )

    async def upload_stream(
        self,
        *,
        path: str,
        content: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> StoredObject:

        stored_path = (
            await self._file_storage.upload_stream(
                path=path,
                content=content,
                content_type=content_type,
            )
        )

        return StoredObject(
            provider_id=(
                self._storage_provider_id
            ),
            path=stored_path,
            content_type=content_type,
            size_bytes=None,
        )