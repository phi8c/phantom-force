from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class StorageAsset:
    id: UUID | None
    document_id: UUID
    storage_provider_id: UUID
    asset_type: str
    storage_path: str
    content_type: str | None
    size_bytes: int | None


class StorageAssetRepository(ABC):

    @abstractmethod
    async def get_by_document_and_type(
        self,
        *,
        document_id: UUID,
        asset_type: str,
    ) -> StorageAsset | None:
        pass

    @abstractmethod
    async def create(
        self,
        asset: StorageAsset,
    ) -> StorageAsset:
        pass
