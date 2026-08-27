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
            batch_id=model.batch_id,
            chunk_id=model.chunk_id,
            sensitivity=model.sensitivity,
            metadata=model.metadata_payload,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: ChunkClassification,
    ) -> ChunkClassificationModel:

        return ChunkClassificationModel(
            id=entity.id,
            batch_id=entity.batch_id,
            chunk_id=entity.chunk_id,
            sensitivity=entity.sensitivity,
            metadata_payload=entity.metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
