from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.download.domain.contracts.storage_asset_repository import (
    StorageAsset,
    StorageAssetRepository,
)

from module.ingest.download.infrastructure.persistence.mappers.storage_asset_mapper import (
    StorageAssetMapper,
)


class StorageAssetRepositoryImpl(
    StorageAssetRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        asset: StorageAsset,
    ) -> StorageAsset:

        model = StorageAssetMapper.to_model(
            asset,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return StorageAssetMapper.to_entity(
            model,
        )