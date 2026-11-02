from typing import Protocol
from uuid import UUID

from module.structured_data.composition import QueryResult


class StructuredReader(Protocol):
    async def query(self, *, knowledge_space_id: UUID, question: str) -> QueryResult | None: ...
