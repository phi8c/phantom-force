from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID


@dataclass
class DownloadSource:
    content: AsyncIterator[bytes]
    file_name: str
    content_type: str | None
    size_bytes: int | None


class DocumentSource(ABC):

    @abstractmethod
    async def open(
        self,
        document_id: UUID,
    ) -> DownloadSource:
        pass