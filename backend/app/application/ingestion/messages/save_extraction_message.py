from dataclasses import dataclass
from uuid import UUID
from app.infrastructure.providers.extraction.docling.models.section import (
    DocumentModel,
)


@dataclass(slots=True)
class SaveExtractionMessage:

    document_id: UUID

    extraction: DocumentModel   