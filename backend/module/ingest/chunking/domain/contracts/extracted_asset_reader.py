from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ExtractedAsset:
    document_id: UUID
    content: AsyncIterator[bytes]
    content_type: str | None
    size_bytes: int | None


class ExtractedAssetReader(ABC):

    @abstractmethod
    async def open_extracted(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> ExtractedAsset:
        pass
