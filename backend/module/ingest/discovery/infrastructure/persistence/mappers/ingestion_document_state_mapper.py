from module.ingest.discovery.domain.entities.ingestion_document_state import (
    IngestionDocumentState,
)

from module.ingest.discovery.domain.enums.ingestion_document_status import (
    IngestionDocumentStatus,
)

from module.ingest.discovery.infrastructure.persistence.models.ingestion_document_state_model import (
    IngestionDocumentStateModel,
)


class IngestionDocumentStateMapper:

    @staticmethod
    def to_entity(model):
        return IngestionDocumentState(
            document_id=model.document_id,
            ingestion_job_id=model.ingestion_job_id,
            status=IngestionDocumentStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity):
        values = {
            "document_id": entity.document_id,
            "ingestion_job_id": entity.ingestion_job_id,
            "status": entity.status.value,
        }

        if entity.created_at is not None:
            values["created_at"] = entity.created_at

        if entity.updated_at is not None:
            values["updated_at"] = entity.updated_at

        return IngestionDocumentStateModel(
            **values,
        )
