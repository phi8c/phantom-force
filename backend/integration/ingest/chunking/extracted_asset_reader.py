from collections.abc import AsyncIterator
from uuid import UUID

from module.ingest.chunking.composition import (
    ExtractedAsset,
    ExtractedAssetReader,
)
from module.ingest.extraction.composition import (
    ExtractedAssetQuery,
)


class StorageExtractedAssetReader(
    ExtractedAssetReader,
):

    def __init__(
        self,
        extracted_asset_query: ExtractedAssetQuery,
        file_storage,
    ):
        self.extracted_asset_query = extracted_asset_query
        self._file_storage = file_storage

    async def open_extracted(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractedAsset:

        asset = await self.extracted_asset_query.get_extracted(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
        )

        if asset is None:
            raise ValueError(
                "EXTRACTED storage asset not found"
            )

        return ExtractedAsset(
            document_id=document_id,
            content=self._open_content(
                asset.storage_path,
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
