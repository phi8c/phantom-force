import logging
from uuid import UUID

from module.ingest.orchestration.domain.contracts import (
    OrchestrationRepository,
)
from module.ingest.orchestration.domain.enums import BatchStatus
from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.orchestration.domain.enums import OrchestrationEventType
from module.ingest.orchestration.domain.enums import StageStatus


logger = logging.getLogger(__name__)


class NoOpOrchestrationProgressService:

    async def create_discovery_batch(
        self,
        *,
        ingestion_job_id: UUID,
        document_ids: list[UUID],
    ) -> UUID | None:
        return None

    async def mark_stage_ready(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        return None

    async def mark_stage_processing(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        return None

    async def mark_stage_completed(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        return None

    async def mark_stage_failed(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
        error: str | None = None,
    ) -> None:
        return None

    async def mark_stage_skipped(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        return None


class OrchestrationProgressService:

    def __init__(
        self,
        repository: OrchestrationRepository,
    ):
        self.repository = repository

    async def create_discovery_batch(
        self,
        *,
        ingestion_job_id: UUID,
        document_ids: list[UUID],
    ) -> UUID | None:

        if not document_ids:
            logger.info(
                "orchestration batch_skipped job_id=%s reason=no_documents",
                ingestion_job_id,
            )
            return None

        result = await self.repository.create_discovery_batch(
            ingestion_job_id=ingestion_job_id,
            document_ids=document_ids,
        )

        batch_id = result.ingestion_batch_id

        if not result.created:
            logger.info(
                "orchestration batch_exists job_id=%s batch_id=%s documents=%s",
                ingestion_job_id,
                batch_id,
                len(document_ids),
            )
            return batch_id

        logger.info(
            "orchestration batch_created job_id=%s batch_id=%s documents=%s",
            ingestion_job_id,
            batch_id,
            len(document_ids),
        )

        await self.repository.append_event(
            ingestion_job_id=ingestion_job_id,
            ingestion_batch_id=batch_id,
            event_type=OrchestrationEventType.BATCH_CREATED,
            payload={
                "total_files": len(document_ids),
            },
        )

        for document_id in document_ids:
            await self.repository.append_event(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch_id,
                document_id=document_id,
                event_type=(
                    OrchestrationEventType
                    .DOCUMENT_STAGE_COMPLETED
                ),
                stage=IngestionStage.DISCOVERY,
                status=StageStatus.COMPLETED,
            )
            await self.repository.append_event(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch_id,
                document_id=document_id,
                event_type=(
                    OrchestrationEventType
                    .DOCUMENT_STAGE_READY
                ),
                stage=IngestionStage.DOWNLOAD,
                status=StageStatus.READY,
            )

        return batch_id

    async def mark_stage_ready(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        await self._mark_stage(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            stage=stage,
            status=StageStatus.READY,
            event_type=(
                OrchestrationEventType
                .DOCUMENT_STAGE_READY
            ),
        )

    async def mark_stage_processing(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        await self._mark_stage(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            stage=stage,
            status=StageStatus.PROCESSING,
            event_type=(
                OrchestrationEventType
                .DOCUMENT_STAGE_PROCESSING
            ),
        )

    async def mark_stage_completed(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        await self._mark_stage(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            stage=stage,
            status=StageStatus.COMPLETED,
            event_type=(
                OrchestrationEventType
                .DOCUMENT_STAGE_COMPLETED
            ),
        )

    async def mark_stage_failed(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
        error: str | None = None,
    ) -> None:
        await self._mark_stage(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            stage=stage,
            status=StageStatus.FAILED,
            event_type=(
                OrchestrationEventType
                .DOCUMENT_STAGE_FAILED
            ),
            error=error,
        )

    async def mark_stage_skipped(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
    ) -> None:
        await self._mark_stage(
            ingestion_job_id=ingestion_job_id,
            document_id=document_id,
            stage=stage,
            status=StageStatus.SKIPPED,
            event_type=(
                OrchestrationEventType
                .DOCUMENT_STAGE_SKIPPED
            ),
        )

    async def _mark_stage(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
        status: StageStatus,
        event_type: OrchestrationEventType,
        error: str | None = None,
    ) -> None:

        batch_id = (
            await self.repository.find_batch_id_for_document(
                ingestion_job_id=ingestion_job_id,
                document_id=document_id,
            )
        )

        if batch_id is None:
            logger.warning(
                "orchestration stage_not_recorded job_id=%s document_id=%s stage=%s status=%s reason=batch_not_found",
                ingestion_job_id,
                document_id,
                stage.value,
                status.value,
            )
            return

        await self.repository.upsert_stage_state(
            ingestion_job_id=ingestion_job_id,
            ingestion_batch_id=batch_id,
            document_id=document_id,
            stage=stage,
            status=status,
            error=error,
        )

        batch_status_result = (
            await self.repository.refresh_batch_status(
                ingestion_batch_id=batch_id,
            )
        )

        await self.repository.append_event(
            ingestion_job_id=ingestion_job_id,
            ingestion_batch_id=batch_id,
            document_id=document_id,
            event_type=event_type,
            stage=stage,
            status=status,
            payload={
                "error": error,
            }
            if error
            else {},
        )
        logger.info(
            "orchestration stage_updated job_id=%s batch_id=%s document_id=%s stage=%s status=%s",
            ingestion_job_id,
            batch_id,
            document_id,
            stage.value,
            status.value,
        )

        if (
            batch_status_result.changed
            and batch_status_result.status
            in {
                BatchStatus.COMPLETED,
                BatchStatus.COMPLETED_WITH_ERRORS,
            }
        ):
            await self.repository.append_event(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch_id,
                event_type=(
                    OrchestrationEventType.BATCH_COMPLETED
                ),
                payload={
                    "status": (
                        batch_status_result.status.value
                    ),
                },
            )
            logger.info(
                "orchestration batch_completed job_id=%s batch_id=%s status=%s",
                ingestion_job_id,
                batch_id,
                batch_status_result.status.value,
            )
