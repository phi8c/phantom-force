from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
)
from module.ingest.extraction.domain.contracts.extracted_asset_query import (
    ExtractedAssetQuery as ExtractedAssetQueryContract,
    ExtractedAssetRecord,
)


class ExtractedAssetQuery(ExtractedAssetQueryContract):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_extracted(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractedAssetRecord | None:

        statement = (
            select(
                StorageAssetModel,
            )
            .where(
                StorageAssetModel.document_id
                == document_id,
                StorageAssetModel.asset_type
                == "EXTRACTED",
                StorageAssetModel.storage_path
                == self._storage_path(
                    ingestion_job_id=ingestion_job_id,
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
            return None

        return ExtractedAssetRecord(
            storage_path=asset.storage_path,
            content_type=asset.content_type,
            size_bytes=asset.size_bytes,
        )

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
