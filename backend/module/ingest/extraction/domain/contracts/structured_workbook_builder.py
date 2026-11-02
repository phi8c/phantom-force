from pathlib import Path
from typing import Protocol
from uuid import UUID


class StructuredWorkbookBuilder(Protocol):
    async def build(self, *, source: Path, file_name: str, document_id: UUID,
                    ingestion_job_id: UUID) -> dict: ...
