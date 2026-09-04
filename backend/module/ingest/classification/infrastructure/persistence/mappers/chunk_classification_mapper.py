from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.infrastructure.persistence.models.chunk_classification_model import (
    ChunkClassificationModel,
)


class ChunkClassificationMapper:

    @staticmethod
    def to_entity(
        model: ChunkClassificationModel,
    ) -> ChunkClassification:

        return ChunkClassification(
            id=model.id,
            chunk_id=model.chunk_id,
            model_name=model.model_name,
            label=model.label,
            confidence=model.confidence,
            raw_response=model.raw_response,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: ChunkClassification,
    ) -> ChunkClassificationModel:

        values = {
            "chunk_id": entity.chunk_id,
            "model_name": entity.model_name,
            "label": entity.label,
            "confidence": entity.confidence,
            "raw_response": entity.raw_response,
        }

        if entity.id is not None:
            values["id"] = entity.id

        if entity.created_at is not None:
            values["created_at"] = entity.created_at

        return ChunkClassificationModel(
            **values,
        )
