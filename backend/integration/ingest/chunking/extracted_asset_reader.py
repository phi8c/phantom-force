from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.domain.contracts.extracted_asset_reader import (
    ExtractedAsset,
    ExtractedAssetReader,
)
from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
)


class StorageExtractedAssetReader(
    ExtractedAssetReader,
):

    def __init__(
        self,
        session: AsyncSession,
        file_storage,
    ):
        self.session = session
        self._file_storage = file_storage

    async def open_extracted(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractedAsset:

        statement = (
            select(
                StorageAssetModel
            )
            .where(
                StorageAssetModel.document_id
                == document_id,
                StorageAssetModel.asset_type
                == "EXTRACTED",
                StorageAssetModel.storage_path
                == self._storage_path(
                    ingestion_job_id=(
                        ingestion_job_id
                    ),
                    document_id=document_id,
                ),
            )
            .order_by(
                StorageAssetModel.created_at.desc(),
            )
            .limit(
                1,
            )
        )

        result = await self.session.execute(
            statement,
        )

        asset = result.scalar_one_or_none()

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

    @staticmethod
    def _storage_path(
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> str:

        return (
            f"ingest/"
            f"{ingestion_job_id}/"
            f"{document_id}/"
            f"extracted.json"
        )
