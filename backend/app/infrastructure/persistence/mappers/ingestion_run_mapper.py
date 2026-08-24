from app.domain.entities.ingestion_run import (
    IngestionRun,
)

from app.infrastructure.persistence.models.ingestion_run_model import (
    IngestionRunModel,
)


class IngestionRunMapper:

    @staticmethod
    def to_entity(
        model: IngestionRunModel,
    ) -> IngestionRun:

        return IngestionRun(
            id=model.id,

            source_id=model.source_id,

            trigger_type=model.trigger_type,

            scope_type=model.scope_type,

            scope_data=model.scope_data,

            status=model.status,

            is_build_graph=model.is_build_graph,

            total_files=model.total_files,

            completed_files=model.completed_files,

            failed_files=model.failed_files,
            
            configuration=model.configuration,
            
            

            started_at=model.started_at,

            finished_at=model.finished_at,

            created_at=model.created_at,
        )

    @staticmethod
    def to_model(
        entity: IngestionRun,
    ) -> IngestionRunModel:

        return IngestionRunModel(
            id=entity.id,

            source_id=entity.source_id,

            trigger_type=entity.trigger_type,

            scope_type=entity.scope_type,

            scope_data=entity.scope_data,

            status=entity.status,

            is_build_graph=entity.is_build_graph,

            total_files=entity.total_files,

            completed_files=entity.completed_files,

            failed_files=entity.failed_files,
            
            configuration=entity.configuration,

            started_at=entity.started_at,

            finished_at=entity.finished_at,

            created_at=entity.created_at,
        )