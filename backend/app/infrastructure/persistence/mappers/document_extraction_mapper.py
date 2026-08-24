from app.domain.entities.document_extraction import (
    DocumentExtraction,
)

from app.infrastructure.persistence.models.document_extraction_model import (
    DocumentExtractionModel,
)


class DocumentExtractionMapper:

    @staticmethod
    def to_domain(
        model: DocumentExtractionModel,
    ) -> DocumentExtraction:

        return DocumentExtraction(
            id=model.id,
            document_id=model.document_id,
            structured_content=(
        model.structured_content
    ),
            page_count=model.page_count,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: DocumentExtraction,
    ) -> DocumentExtractionModel:

        return DocumentExtractionModel(
            id=entity.id,
            document_id=entity.document_id,
             structured_content=(
        entity.structured_content
    ),
            page_count=entity.page_count,
            created_at=entity.created_at,
        )