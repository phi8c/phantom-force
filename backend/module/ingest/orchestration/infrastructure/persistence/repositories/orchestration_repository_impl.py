from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.config.infrastructure.persistence.models.ingestion_job_model import (
    IngestionJobModel,
)
from module.ingest.orchestration.domain.contracts import (
    OrchestrationRepository,
)
from module.ingest.orchestration.domain.enums import BatchStatus
from module.ingest.orchestration.domain.entities import (
    BatchStatusRefreshResult,
)
from module.ingest.orchestration.domain.entities import (
    DiscoveryBatchCreationResult,
)
from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.orchestration.domain.enums import OrchestrationEventType
from module.ingest.orchestration.domain.enums import StageStatus
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionBatchDocumentModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionBatchModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionDocumentStageStateModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionOrchestrationEventModel,
)


class OrchestrationRepositoryImpl(OrchestrationRepository):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_discovery_batch(
        self,
        *,
        ingestion_job_id: UUID,
        document_ids: list[UUID],
    ) -> DiscoveryBatchCreationResult:

        existing_batch_id = (
            await self._find_existing_batch_for_documents(
                ingestion_job_id=ingestion_job_id,
                document_ids=document_ids,
            )
        )

        if existing_batch_id is not None:
            return DiscoveryBatchCreationResult(
                ingestion_batch_id=existing_batch_id,
                created=False,
            )

        await self._lock_ingestion_job(
            ingestion_job_id,
        )

        existing_batch_id = (
            await self._find_existing_batch_for_documents(
                ingestion_job_id=ingestion_job_id,
                document_ids=document_ids,
            )
        )

        if existing_batch_id is not None:
            return DiscoveryBatchCreationResult(
                ingestion_batch_id=existing_batch_id,
                created=False,
            )

        batch_index = await self._next_batch_index(
            ingestion_job_id,
        )

        now = datetime.now(timezone.utc)

        batch = IngestionBatchModel(
            ingestion_job_id=ingestion_job_id,
            batch_index=batch_index,
            status=BatchStatus.PROCESSING.value,
            total_files=len(document_ids),
            completed_files=0,
            failed_files=0,
            discovery_completed_at=now,
            updated_at=now,
        )

        self.session.add(batch)
        await self.session.flush()

        if batch.id is None:
            raise ValueError(
                "Ingestion batch id was not generated"
            )

        for ordinal, document_id in enumerate(document_ids):
            await self._insert_membership(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch.id,
                document_id=document_id,
                ordinal=ordinal,
            )
            await self.upsert_stage_state(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch.id,
                document_id=document_id,
                stage=IngestionStage.DISCOVERY,
                status=StageStatus.COMPLETED,
            )
            await self.upsert_stage_state(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=batch.id,
                document_id=document_id,
                stage=IngestionStage.DOWNLOAD,
                status=StageStatus.READY,
            )

        await self.session.flush()

        return DiscoveryBatchCreationResult(
            ingestion_batch_id=batch.id,
            created=True,
        )

    async def find_batch_id_for_document(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> UUID | None:

        statement = select(
            IngestionBatchDocumentModel.ingestion_batch_id
        ).where(
            IngestionBatchDocumentModel.ingestion_job_id
            == ingestion_job_id,
            IngestionBatchDocumentModel.document_id
            == document_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def upsert_stage_state(
        self,
        *,
        ingestion_job_id: UUID,
        ingestion_batch_id: UUID,
        document_id: UUID,
        stage: IngestionStage,
        status: StageStatus,
        error: str | None = None,
    ) -> None:

        now = datetime.now(timezone.utc)

        values = {
            "ingestion_job_id": ingestion_job_id,
            "ingestion_batch_id": ingestion_batch_id,
            "document_id": document_id,
            "stage": stage.value,
            "status": status.value,
            "started_at": (
                now
                if status is StageStatus.PROCESSING
                else None
            ),
            "completed_at": (
                now
                if status
                in {
                    StageStatus.COMPLETED,
                    StageStatus.FAILED,
                    StageStatus.SKIPPED,
                }
                else None
            ),
            "error": error,
            "updated_at": now,
        }

        statement = insert(
            IngestionDocumentStageStateModel
        ).values(
            **values
        )

        update_values = {
            "status": status.value,
            "updated_at": now,
            "error": error,
        }

        if status is StageStatus.PROCESSING:
            update_values["started_at"] = now
            update_values["completed_at"] = None

        if status in {
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.SKIPPED,
        }:
            update_values["completed_at"] = now

        if status in {
            StageStatus.PENDING,
            StageStatus.READY,
        }:
            update_values["completed_at"] = None

        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    "ingestion_job_id",
                    "document_id",
                    "stage",
                ],
                set_=update_values,
            )
        )

    async def refresh_batch_status(
        self,
        *,
        ingestion_batch_id: UUID,
    ) -> BatchStatusRefreshResult:

        batch = await self.session.get(
            IngestionBatchModel,
            ingestion_batch_id,
        )

        if batch is None:
            raise ValueError(
                "Ingestion batch not found"
            )

        required_stages = {
            IngestionStage.DISCOVERY.value,
            IngestionStage.DOWNLOAD.value,
            IngestionStage.EXTRACTION.value,
            IngestionStage.CHUNKING.value,
            IngestionStage.EMBEDDING.value,
            IngestionStage.CLASSIFICATION.value,
        }

        statement = select(
            IngestionDocumentStageStateModel.document_id,
            IngestionDocumentStageStateModel.stage,
            IngestionDocumentStageStateModel.status,
        ).where(
            IngestionDocumentStageStateModel.ingestion_batch_id
            == ingestion_batch_id,
            IngestionDocumentStageStateModel.stage.in_(
                required_stages
            ),
        )

        result = await self.session.execute(statement)

        states_by_document: dict[
            UUID,
            dict[str, str],
        ] = {}

        for row in result.all():
            states_by_document.setdefault(
                row.document_id,
                {},
            )[row.stage] = row.status

        (
            completed_files,
            failed_files,
            next_status,
        ) = self._summarize_batch_completion(
            total_files=batch.total_files,
            states_by_document=states_by_document,
            required_stages=required_stages,
        )

        previous_status = BatchStatus(
            batch.status
        )

        batch.completed_files = completed_files
        batch.failed_files = failed_files
        batch.status = next_status.value
        batch.updated_at = datetime.now(timezone.utc)

        if next_status in {
            BatchStatus.COMPLETED,
            BatchStatus.COMPLETED_WITH_ERRORS,
        }:
            batch.completed_at = batch.updated_at

        await self.session.flush()

        return BatchStatusRefreshResult(
            status=next_status,
            changed=previous_status != next_status,
        )

    @staticmethod
    def _summarize_batch_completion(
        *,
        total_files: int,
        states_by_document: dict[UUID, dict[str, str]],
        required_stages: set[str],
    ) -> tuple[int, int, BatchStatus]:

        completed_files = 0
        failed_files = 0

        for stage_states in states_by_document.values():
            has_failed = any(
                status == StageStatus.FAILED.value
                for status in stage_states.values()
            )

            if has_failed:
                failed_files += 1
                continue

            satisfied = all(
                stage_states.get(stage)
                in {
                    StageStatus.COMPLETED.value,
                    StageStatus.SKIPPED.value,
                }
                for stage in required_stages
            )

            if satisfied:
                completed_files += 1

        status = BatchStatus.PROCESSING

        if completed_files + failed_files >= total_files:
            if failed_files > 0:
                status = BatchStatus.COMPLETED_WITH_ERRORS
            else:
                status = BatchStatus.COMPLETED

        return (
            completed_files,
            failed_files,
            status,
        )

    async def append_event(
        self,
        *,
        ingestion_job_id: UUID,
        event_type: OrchestrationEventType,
        ingestion_batch_id: UUID | None = None,
        document_id: UUID | None = None,
        stage: IngestionStage | None = None,
        status: StageStatus | None = None,
        payload: dict | None = None,
    ) -> None:

        self.session.add(
            IngestionOrchestrationEventModel(
                ingestion_job_id=ingestion_job_id,
                ingestion_batch_id=ingestion_batch_id,
                document_id=document_id,
                event_type=event_type.value,
                stage=stage.value if stage else None,
                status=status.value if status else None,
                payload=payload or {},
            )
        )

        await self.session.flush()

    async def _find_existing_batch_for_documents(
        self,
        *,
        ingestion_job_id: UUID,
        document_ids: list[UUID],
    ) -> UUID | None:

        statement = select(
            IngestionBatchDocumentModel.ingestion_batch_id
        ).where(
            IngestionBatchDocumentModel.ingestion_job_id
            == ingestion_job_id,
            IngestionBatchDocumentModel.document_id.in_(
                document_ids
            ),
        )

        result = await self.session.execute(statement)

        return result.scalars().first()

    async def _lock_ingestion_job(
        self,
        ingestion_job_id: UUID,
    ) -> None:

        statement = select(
            IngestionJobModel.id
        ).where(
            IngestionJobModel.id == ingestion_job_id,
        ).with_for_update()

        await self.session.execute(statement)

    async def _next_batch_index(
        self,
        ingestion_job_id: UUID,
    ) -> int:

        statement = select(
            func.coalesce(
                func.max(
                    IngestionBatchModel.batch_index
                ),
                0,
            )
            + 1
        ).where(
            IngestionBatchModel.ingestion_job_id
            == ingestion_job_id,
        )

        result = await self.session.execute(statement)

        return int(result.scalar_one())

    async def _insert_membership(
        self,
        *,
        ingestion_job_id: UUID,
        ingestion_batch_id: UUID,
        document_id: UUID,
        ordinal: int,
    ) -> None:

        statement = insert(
            IngestionBatchDocumentModel
        ).values(
            ingestion_job_id=ingestion_job_id,
            ingestion_batch_id=ingestion_batch_id,
            document_id=document_id,
            ordinal=ordinal,
        )

        await self.session.execute(
            statement.on_conflict_do_nothing(
                index_elements=[
                    "ingestion_job_id",
                    "document_id",
                ],
            )
        )
