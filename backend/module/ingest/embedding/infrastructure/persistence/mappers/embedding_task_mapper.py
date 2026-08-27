from module.ingest.embedding.domain.entities.embedding_task import (
    EmbeddingTask,
)
from module.ingest.embedding.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.embedding.infrastructure.persistence.models.embedding_task_model import (
    EmbeddingTaskModel,
)


class EmbeddingTaskMapper:

    @staticmethod
    def to_entity(
        model: EmbeddingTaskModel,
    ) -> EmbeddingTask:

        return EmbeddingTask(
            id=model.id,
            ingestion_job_id=model.ingestion_job_id,
            batch_id=model.batch_id,
            document_id=model.document_id,
            status=TaskStatus(
                model.status
            ),
            attempt_count=model.attempt_count,
            claimed_by=model.claimed_by,
            lease_until=model.lease_until,
            error=model.error,
            created_at=model.created_at,
            updated_at=model.updated_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def to_model(
        entity: EmbeddingTask,
    ) -> EmbeddingTaskModel:

        return EmbeddingTaskModel(
            id=entity.id,
            ingestion_job_id=entity.ingestion_job_id,
            batch_id=entity.batch_id,
            document_id=entity.document_id,
            status=entity.status.value,
            attempt_count=entity.attempt_count,
            claimed_by=entity.claimed_by,
            lease_until=entity.lease_until,
            error=entity.error,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            completed_at=entity.completed_at,
        )
