from module.ingest.chunking.domain.entities.chunking_task import (
    ChunkingTask,
)
from module.ingest.chunking.domain.enums.task_status import (
    TaskStatus,
)
from module.ingest.chunking.infrastructure.persistence.models.chunking_task_model import (
    ChunkingTaskModel,
)


class ChunkingTaskMapper:

    @staticmethod
    def to_entity(
        model: ChunkingTaskModel,
    ) -> ChunkingTask:

        return ChunkingTask(
            id=model.id,
            ingestion_job_id=model.ingestion_job_id,
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
        entity: ChunkingTask,
    ) -> ChunkingTaskModel:

        return ChunkingTaskModel(
            id=entity.id,
            ingestion_job_id=(
                entity.ingestion_job_id
            ),
            document_id=(
                entity.document_id
            ),
            status=(
                entity.status.value
            ),
            attempt_count=(
                entity.attempt_count
            ),
            claimed_by=(
                entity.claimed_by
            ),
            lease_until=(
                entity.lease_until
            ),
            error=entity.error,
            created_at=(
                entity.created_at
            ),
            updated_at=(
                entity.updated_at
            ),
            completed_at=(
                entity.completed_at
            ),
        )
