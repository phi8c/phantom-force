from module.ingest.discovery.domain.entities.document import Document

from module.ingest.discovery.infrastructure.persistence.models.document_model import (
    DocumentModel,
)


class DocumentMapper:

    @staticmethod
    def to_entity(model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            data_hub_id=model.data_hub_id,
            external_file_id=model.external_file_id,
            provider_metadata=model.provider_metadata,
            file_name=model.file_name,
            department=model.department,
            owner_role=model.owner_role,
            security_level=model.security_level,
            document_type=model.document_type,
            source_file_url=model.source_file_url,
            file_extension=model.file_extension,
            file_size_bytes=model.file_size_bytes,
            original_file_path=model.original_file_path,
            last_modified_at=model.last_modified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Document) -> DocumentModel:
        return DocumentModel(
            id=entity.id,
            data_hub_id=entity.data_hub_id,
            external_file_id=entity.external_file_id,
            provider_metadata=entity.provider_metadata,
            file_name=entity.file_name,
            department=entity.department,
            owner_role=entity.owner_role,
            security_level=entity.security_level,
            document_type=entity.document_type,
            source_file_url=entity.source_file_url,
            file_extension=entity.file_extension,
            file_size_bytes=entity.file_size_bytes,
            original_file_path=entity.original_file_path,
            last_modified_at=entity.last_modified_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )