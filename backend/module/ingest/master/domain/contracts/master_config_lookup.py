from typing import Protocol
from uuid import UUID


class MasterConfigLookup(Protocol):
    async def lookup(self, extraction_code: str, chunking_code: str,
                     model_set_code: str | None) -> tuple[UUID | None, UUID | None, UUID | None]: ...
