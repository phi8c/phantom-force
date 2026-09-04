from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SourceAssetRecord:
    file_name: str
    storage_path: str
    content_type: str | None
    size_bytes: int | None


class SourceAssetQuery(ABC):

    @abstractmethod
    async def get_latest_source(
        self,
        document_id: UUID,
    ) -> SourceAssetRecord | None:
        pass
