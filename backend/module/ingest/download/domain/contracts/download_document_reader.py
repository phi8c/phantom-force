from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class DownloadDocument:
    id: UUID
    file_name: str
    file_size_bytes: int | None
    file_extension: str | None
    source_file_url: str | None
    provider_metadata: dict


class DownloadDocumentReader(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        document_id: UUID,
    ) -> DownloadDocument | None:
        ...