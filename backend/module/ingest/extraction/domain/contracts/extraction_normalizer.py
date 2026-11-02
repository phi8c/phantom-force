from typing import Any, Protocol

from shared.ingestion.document import ExtractedDocumentV2


class ExtractionNormalizer(Protocol):
    """Normalize engine output or legacy assets, preserving text and tables.

    Versionless persisted assets mean legacy v1; unknown versions must fail.
    Provider implementations belong to extraction infrastructure.
    """

    def normalize(self, payload: dict[str, Any], *, document_id: str) -> ExtractedDocumentV2:
        ...
