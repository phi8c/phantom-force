from module.ingest.download.domain.contracts.storage_asset_repository import (
    StorageAsset,
)

from module.ingest.download.infrastructure.persistence.models.storage_asset_model import (
    StorageAssetModel,
)


class StorageAssetMapper:

    @staticmethod
    def to_entity(
        model: StorageAssetModel,
    ) -> StorageAsset:

        return StorageAsset(
            id=model.id,
            document_id=model.document_id,
            storage_provider_id=model.storage_provider_id,
            asset_type=model.asset_type,
            storage_path=model.storage_path,
            content_type=model.content_type,
            size_bytes=model.size_bytes,
        )

    @staticmethod
    def to_model(
        entity: StorageAsset,
    ) -> StorageAssetModel:

        return StorageAssetModel(
            id=entity.id,
            document_id=entity.document_id,
            storage_provider_id=(
                entity.storage_provider_id
            ),
            asset_type=entity.asset_type,
            storage_path=entity.storage_path,
            content_type=entity.content_type,
            size_bytes=entity.size_bytes,
        )