from module.ingest.embedding.domain.entities.document_chunk_embedding import (
    DocumentChunkEmbedding,
)
from module.ingest.embedding.infrastructure.persistence.models.document_chunk_embedding_model import (
    DocumentChunkEmbeddingModel,
)


class DocumentChunkEmbeddingMapper:

    @staticmethod
    def to_entity(
        model: DocumentChunkEmbeddingModel,
    ) -> DocumentChunkEmbedding:

        return DocumentChunkEmbedding(
            id=model.id,
            chunk_id=model.chunk_id,
            model_name=model.model_name,
            embedding=model.embedding,
            dimension=model.dimension,
            token_count=model.token_count,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: DocumentChunkEmbedding,
    ) -> DocumentChunkEmbeddingModel:

        return DocumentChunkEmbeddingModel(
            id=entity.id,
            chunk_id=entity.chunk_id,
            model_name=entity.model_name,
            embedding=entity.embedding,
            dimension=entity.dimension,
            token_count=entity.token_count,
            created_at=entity.created_at,
        )
