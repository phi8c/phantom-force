from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ExtractedAssetRecord:
    storage_path: str
    content_type: str | None
    size_bytes: int | None


class ExtractedAssetQuery(ABC):

    @abstractmethod
    async def get_extracted(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractedAssetRecord | None:
        pass
