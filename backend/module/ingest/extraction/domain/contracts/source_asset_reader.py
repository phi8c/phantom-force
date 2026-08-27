from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SourceAsset:
    document_id: UUID
    file_name: str
    content: AsyncIterator[bytes]
    content_type: str | None
    size_bytes: int | None


class SourceAssetReader(ABC):

    @abstractmethod
    async def open_source(
        self,
        document_id: UUID,
    ) -> SourceAsset:
        pass
