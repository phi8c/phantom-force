from app.domain.entities.chunk_batch import (
    ChunkBatch,
)

from app.infrastructure.persistence.models.chunk_batch_model import (
    ChunkBatchModel,
)


class ChunkBatchMapper:

    @staticmethod
    def to_domain(
        model: ChunkBatchModel,
    ) -> ChunkBatch:

        return ChunkBatch(
            id=model.id,
            document_id=model.document_id,
            batch_index=model.batch_index,
            total_chunks=model.total_chunks,
            classification_completed=model.classification_completed,
            embedding_completed=model.embedding_completed,
            batch_completed=model.batch_completed,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: ChunkBatch,
    ) -> ChunkBatchModel:

        return ChunkBatchModel(
            id=entity.id,
            document_id=entity.document_id,
            batch_index=entity.batch_index,
            total_chunks=entity.total_chunks,
            
            classification_completed=entity.classification_completed,
            embedding_completed=entity.embedding_completed,
            batch_completed=entity.batch_completed,
            created_at=entity.created_at,
        )