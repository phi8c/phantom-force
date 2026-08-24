from app.domain.entities.document_processing_task import (
    DocumentProcessingTask,
)

from app.infrastructure.persistence.models.document_processing_task import (
    DocumentProcessingTask as DocumentProcessingTaskModel,
)


class DocumentProcessingTaskMapper:

    @staticmethod
    def to_entity(
        model: DocumentProcessingTaskModel,
    ) -> DocumentProcessingTask:

        return DocumentProcessingTask(
            id=model.id,
            document_id=model.document_id,
            batch_id=model.batch_id,
            task_type=model.task_type,
            status=model.status,
            retry_count=model.retry_count,
            error_message=model.error_message,
            started_at=model.started_at,
            finished_at=model.finished_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
       

    @staticmethod
    def to_model(
        entity: DocumentProcessingTask,
    ) -> DocumentProcessingTaskModel:

        return (
            DocumentProcessingTaskModel(
                id=entity.id,
                document_id=entity.document_id,
                batch_id=entity.batch_id,
                task_type=entity.task_type,
                status=entity.status,
                retry_count=entity.retry_count,
                error_message=entity.error_message,
                started_at=entity.started_at,
                finished_at=entity.finished_at,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )