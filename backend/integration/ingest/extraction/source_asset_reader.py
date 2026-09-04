from collections.abc import AsyncIterator
from uuid import UUID

from module.ingest.download.domain.contracts.source_asset_query import (
    SourceAssetQuery,
)
from module.ingest.extraction.domain.contracts.source_asset_reader import (
    SourceAsset,
    SourceAssetReader,
)


class StorageSourceAssetReader(
    SourceAssetReader,
):

    def __init__(
        self,
        source_asset_query: SourceAssetQuery,
        file_storage,
    ):
        self.source_asset_query = source_asset_query
        self._file_storage = file_storage

    async def open_source(
        self,
        document_id: UUID,
    ) -> SourceAsset:

        asset = await self.source_asset_query.get_latest_source(
            document_id,
        )

        if asset is None:
            raise ValueError(
                "SOURCE storage asset not found"
            )

        return SourceAsset(
            document_id=document_id,
            file_name=asset.file_name,
            content=(
                self._open_content(
                    asset.storage_path,
                )
            ),
            content_type=asset.content_type,
            size_bytes=asset.size_bytes,
        )

    async def _open_content(
        self,
        path: str,
    ) -> AsyncIterator[bytes]:

        download_stream = getattr(
            self._file_storage,
            "download_stream",
            None,
        )

        if download_stream is not None:
            async for chunk in download_stream(
                path=path,
            ):
                yield chunk
            return

        content = await self._file_storage.download(
            path,
        )

        yield content
