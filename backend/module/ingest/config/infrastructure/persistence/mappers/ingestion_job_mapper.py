from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)

from module.ingest.config.infrastructure.persistence.models.ingestion_job_model import (
    IngestionJobModel,
)


class IngestionJobMapper:

    @staticmethod
    def to_entity(
        model: IngestionJobModel,
    ) -> IngestionJob:

        return IngestionJob(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            trigger_type=model.trigger_type,
            status=model.status,
            is_build_graph=model.is_build_graph,
            total_files=model.total_files,
            completed_files=model.completed_files,
            failed_files=model.failed_files,
            started_at=model.started_at,
            finished_at=model.finished_at,
            created_at=model.created_at,
            scope_type=model.scope_type,
            scope_data=model.scope_data,
        )

    @staticmethod
    def to_model(
        entity: IngestionJob,
    ) -> IngestionJobModel:

        return IngestionJobModel(
            id=entity.id,
            knowledge_space_id=entity.knowledge_space_id,
            trigger_type=entity.trigger_type,
            status=entity.status,
            is_build_graph=entity.is_build_graph,
            total_files=entity.total_files,
            completed_files=entity.completed_files,
            failed_files=entity.failed_files,
            started_at=entity.started_at,
            finished_at=entity.finished_at,
            created_at=entity.created_at,
            scope_type=entity.scope_type,
            scope_data=entity.scope_data,
        )