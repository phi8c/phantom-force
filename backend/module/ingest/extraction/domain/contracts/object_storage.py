from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StoredObject:
    provider_id: UUID
    path: str
    content_type: str | None
    size_bytes: int | None


class ObjectStorage(ABC):

    @abstractmethod
    async def upload_stream(
        self,
        *,
        path: str,
        content: AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> StoredObject:
        pass
