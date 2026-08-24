from app.domain.entities.document_chunk_classification import (
    DocumentChunkClassification,
)

from app.infrastructure.persistence.models.document_chunk_classification_model import (
    DocumentChunkClassificationModel,
)


class DocumentChunkClassificationMapper:

    @staticmethod
    def to_domain(
        model: DocumentChunkClassificationModel,
    ) -> DocumentChunkClassification:

        return DocumentChunkClassification(
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
        entity: DocumentChunkClassification,
    ) -> DocumentChunkClassificationModel:

        return DocumentChunkClassificationModel(
            id=entity.id,
            chunk_id=entity.chunk_id,
            model_name=entity.model_name,
            label=entity.label,
            confidence=entity.confidence,
            raw_response=entity.raw_response,
            created_at=entity.created_at,
        )