from datetime import datetime
from datetime import timezone

from module.ingest.config.application.dtos.create_ingestion_job import (
    CreateIngestionJobCommand,
    CreateIngestionJobResult,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)
from module.ingest.config.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.config.domain.entities.ingestion_job import (
    IngestionJob,
)


class CreateIngestionJobUseCase:

    def __init__(
        self,
        *,
        ingestion_config_repository: IngestionConfigRepository,
        uow: UnitOfWork,
    ):
        self.ingestion_config_repository = (
            ingestion_config_repository
        )
        self.uow = uow

    async def execute(
        self,
        command: CreateIngestionJobCommand,
    ) -> CreateIngestionJobResult:

        trigger_type = command.trigger_type.strip().upper()

        if not trigger_type:
            raise ValueError(
                "trigger_type must not be empty"
            )

        now = datetime.now(
            timezone.utc,
        )

        try:
            job = await self.ingestion_config_repository.add_job(
                IngestionJob(
                    id=None,
                    knowledge_space_id=command.knowledge_space_id,
                    trigger_type=trigger_type,
                    status=None,
                    is_build_graph=command.is_build_graph,
                    total_files=0,
                    completed_files=0,
                    failed_files=0,
                    started_at=None,
                    finished_at=None,
                    created_at=now,
                    scope_type=None,
                    scope_data=None,
                )
            )

            await self.uow.commit()

        except Exception:
            await self.uow.rollback()
            raise

        if job.id is None:
            raise RuntimeError(
                "ingestion job id was not generated"
            )

        return CreateIngestionJobResult(
            ingestion_job_id=job.id,
        )
