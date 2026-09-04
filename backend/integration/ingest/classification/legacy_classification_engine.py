from collections.abc import Sequence
from typing import Any

from module.ingest.classification.application.dtos.schemas.engine import (
    ClassificationEngine as LegacyClassificationEngineContract,
)
from module.ingest.classification.application.dtos.schemas.engine import (
    ClassificationResult as LegacyClassificationResult,
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


class RuleBasedLegacyClassificationEngine(
    LegacyClassificationEngineContract,
):

    async def classify(
        self,
        chunks: Sequence[LegacyChunk],
    ) -> Sequence[LegacyClassificationResult]:

        return [
            LegacyClassificationResult(
                chunk_id=chunk.id,
                sensitivity=1,
                metadata={
                    "label": "public",
                    "confidence": 1.0,
                    "model_name": "rule_based_default",
                    "raw_response": None,
                },
            )
            for chunk in chunks
        ]


class LegacyClassificationEngineAdapter(
    ClassificationEngine,
):

    def __init__(
        self,
        engine: (
            LegacyClassificationEngineContract
            | None
        ) = None,
    ):
        self._engine = (
            engine
            or RuleBasedLegacyClassificationEngine()
        )

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

        results = await self._engine.classify(
            legacy_chunks,
        )

        return [
            ClassificationResult(
                chunk_id=result.chunk_id,
                model_name=self._model_name_from_result(
                    result,
                ),
                label=self._label_from_result(
                    result,
                ),
                confidence=self._confidence_from_result(
                    result,
                ),
                raw_response=self._raw_response_from_result(
                    result,
                ),
            )
            for result in results
        ]

    @staticmethod
    def _model_name_from_result(
        result,
    ) -> str:

        metadata = dict(
            result.metadata
            or {}
        )

        model_name = metadata.get(
            "model_name",
        )

        if model_name:
            return str(model_name)

        return "legacy_classification_engine"

    @staticmethod
    def _label_from_result(
        result,
    ) -> str:

        metadata = dict(
            result.metadata
            or {}
        )

        label = metadata.get(
            "label",
        )

        if label:
            return str(label)

        return (
            "public"
            if result.sensitivity <= 1
            else "sensitive"
        )

    @staticmethod
    def _confidence_from_result(
        result,
    ) -> float | None:

        metadata = dict(
            result.metadata
            or {}
        )

        confidence = metadata.get(
            "confidence",
        )

        if confidence is None:
            return None

        return float(confidence)

    @staticmethod
    def _raw_response_from_result(
        result,
    ) -> dict[str, Any] | None:

        metadata = dict(
            result.metadata
            or {}
        )

        raw_response = metadata.get(
            "raw_response",
        )

        if raw_response is None:
            return metadata

        if isinstance(
            raw_response,
            dict,
        ):
            return raw_response

        return {
            "value": raw_response,
        }
