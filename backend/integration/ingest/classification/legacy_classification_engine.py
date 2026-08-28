from typing import Any

from module.ingest.classification.application.dtos.schemas.engine import (
    ClassificationEngine as LegacyClassificationEngine,
)
from module.ingest.classification.application.dtos.schemas.schemas import (
    Chunk as LegacyChunk,
)

from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkForClassification,
)
from module.ingest.classification.domain.contracts.classification_engine import (
    ClassificationEngine,
    ClassificationResult,
)


class LegacyClassificationEngineAdapter(
    ClassificationEngine,
):

    def __init__(
        self,
        engine: LegacyClassificationEngine | None = None,
    ):
        self._engine = engine or LegacyClassificationEngine()

    async def classify_batch(
        self,
        chunks: list[ChunkForClassification],
    ) -> list[ClassificationResult]:

        legacy_chunks = [
            LegacyChunk(
                id=chunk.id,
                content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]

        results = await self._engine.classify_batch(
            legacy_chunks,
        )

        return [
            ClassificationResult(
                chunk_id=result.chunk_id,
                sensitivity=self._sensitivity_from_label(
                    result.label,
                ),
                metadata=self._metadata_from_result(
                    result,
                ),
            )
            for result in results
        ]

    @staticmethod
    def _sensitivity_from_label(
        label: str | None,
    ) -> int:

        normalized = (
            label
            or ""
        ).strip().lower()

        if normalized in {
            "secret",
            "critical",
            "highly_confidential",
        }:
            return 4

        if normalized in {
            "confidential",
            "restricted",
            "high",
            "sensitive",
        }:
            return 3

        if normalized in {
            "internal",
            "medium",
        }:
            return 2

        return 1

    @staticmethod
    def _metadata_from_result(
        result,
    ) -> dict[str, Any]:

        return {
            "label": result.label,
            "confidence": result.confidence,
            "model_name": result.model_name,
            "raw_response": result.raw_response,
        }
