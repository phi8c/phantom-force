from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class PipelineContext:
    """
    Shared context flowing through
    the ingestion pipeline.

    Each stage can enrich the context
    without changing event contracts.
    """

    document_id: UUID

    payload: Any

    metadata: dict[str, Any] | None = None

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        if not self.metadata:
            return default

        return self.metadata.get(
            key,
            default,
        )

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        if self.metadata is None:
            self.metadata = {}

        self.metadata[key] = value