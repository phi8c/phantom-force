from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.infrastructure.persistence.readers.download_document_reader_impl import (
    DownloadDocumentReaderImpl,
)
from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
)
from module.ingest.download.domain.contracts.source_asset_query import (
    SourceAssetQuery as SourceAssetQueryContract,
    SourceAssetRecord,
)


class SourceAssetQuery(SourceAssetQueryContract):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_latest_source(
        self,
        document_id: UUID,
    ) -> SourceAssetRecord | None:

        statement = (
            select(
                StorageAssetModel,
            )
            .where(
                StorageAssetModel.document_id
                == document_id,
                StorageAssetModel.asset_type
                == "SOURCE",
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

        row = result.one_or_none()

        if row is None:
            return None

        asset_model = row[0]
        document_reader = DownloadDocumentReaderImpl(
            session=self.session,
        )
        document = await document_reader.get_by_id(
            document_id,
        )

        if document is None:
            return None

        return SourceAssetRecord(
            file_name=document.file_name,
            storage_path=asset_model.storage_path,
            content_type=asset_model.content_type,
            size_bytes=asset_model.size_bytes,
        )
