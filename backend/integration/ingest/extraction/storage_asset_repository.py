from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
)
from module.ingest.extraction.domain.contracts.storage_asset_repository import (
    StorageAsset,
    StorageAssetRepository,
)


class ModuleStorageAssetRepository(
    StorageAssetRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_document_and_type(
        self,
        *,
        document_id: UUID,
        asset_type: str,
    ) -> StorageAsset | None:

        statement = (
            select(
                StorageAssetModel
            )
            .where(
                StorageAssetModel.document_id
                == document_id,
                StorageAssetModel.asset_type
                == asset_type,
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

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(
            model,
        )

    async def create(
        self,
        asset: StorageAsset,
    ) -> StorageAsset:

        model = StorageAssetModel(
            id=asset.id,
            document_id=asset.document_id,
            storage_provider_id=(
                asset.storage_provider_id
            ),
            asset_type=asset.asset_type,
            storage_path=asset.storage_path,
            content_type=asset.content_type,
            size_bytes=asset.size_bytes,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return self._to_entity(
            model,
        )

    @staticmethod
    def _to_entity(
        model: StorageAssetModel,
    ) -> StorageAsset:

        return StorageAsset(
            id=model.id,
            document_id=model.document_id,
            storage_provider_id=(
                model.storage_provider_id
            ),
            asset_type=model.asset_type,
            storage_path=model.storage_path,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
        )
