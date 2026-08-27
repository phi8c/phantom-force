from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.discovery.infrastructure.persistence.models.document_model import (
    DocumentModel,
)
from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
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
        session: AsyncSession,
        file_storage,
    ):
        self.session = session
        self._file_storage = file_storage

    async def open_source(
        self,
        document_id: UUID,
    ) -> SourceAsset:

        statement = (
            select(
                StorageAssetModel,
                DocumentModel,
            )
            .join(
                DocumentModel,
                DocumentModel.id
                == StorageAssetModel.document_id,
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
            raise ValueError(
                "SOURCE storage asset not found"
            )

        asset_model, document_model = row

        return SourceAsset(
            document_id=document_id,
            file_name=document_model.file_name,
            content=(
                self._open_content(
                    asset_model.storage_path,
                )
            ),
            content_type=asset_model.content_type,
            size_bytes=asset_model.size_bytes,
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
