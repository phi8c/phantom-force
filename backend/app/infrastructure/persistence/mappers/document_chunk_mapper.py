from app.domain.entities.document_chunk import (
    DocumentChunk,
)

from app.infrastructure.persistence.models.document_chunk_model import (
    DocumentChunkModel,
)


class DocumentChunkMapper:

    @staticmethod
    def to_domain(
        model: DocumentChunkModel,
    ) -> DocumentChunk:

        return DocumentChunk(
            id=model.id,
            batch_id=model.batch_id,
            document_id=model.document_id,
            chunk_index=model.chunk_index,
            title=model.title,
            content=model.content,
            metadata=model.metadata_payload,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: DocumentChunk,
    ) -> DocumentChunkModel:

        return DocumentChunkModel(
            id=entity.id,
            batch_id=entity.batch_id,
            document_id=entity.document_id,
            chunk_index=entity.chunk_index,
            title=entity.title,
            content=entity.content,
            metadata_payload=entity.metadata,
            created_at=entity.created_at,
        )