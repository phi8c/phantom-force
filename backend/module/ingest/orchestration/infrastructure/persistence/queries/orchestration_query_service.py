from uuid import UUID

from sqlalchemy import case
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.orchestration.application.dtos import BatchSummary
from module.ingest.orchestration.application.dtos import BatchDocumentView
from module.ingest.orchestration.application.dtos import (
    DocumentStageStateView,
)
from module.ingest.orchestration.application.dtos import (
    OrchestrationEventView,
)
from module.ingest.orchestration.application.dtos import StageCount
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionBatchModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionDocumentStageStateModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionOrchestrationEventModel,
)
from module.ingest.orchestration.infrastructure.persistence.models import (
    IngestionBatchDocumentModel,
)
from module.ingest.orchestration.domain.enums import IngestionStage
from module.ingest.discovery.infrastructure.persistence.models.document_model import (
    DocumentModel,
)


class OrchestrationQueryService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_batches(
        self,
        *,
        ingestion_job_id: UUID,
    ) -> list[BatchSummary]:

        statement = (
            select(IngestionBatchModel)
            .where(
                IngestionBatchModel.ingestion_job_id
                == ingestion_job_id,
            )
            .order_by(
                IngestionBatchModel.batch_index.asc(),
            )
        )

        result = await self.session.execute(statement)

        return [
            BatchSummary(
                id=model.id,
                batch_index=model.batch_index,
                status=model.status,
                total_files=model.total_files,
                completed_files=model.completed_files,
                failed_files=model.failed_files,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            for model in result.scalars().all()
        ]

    async def count_stages(
        self,
        *,
        ingestion_job_id: UUID,
    ) -> list[StageCount]:

        statement = (
            select(
                IngestionDocumentStageStateModel.stage,
                IngestionDocumentStageStateModel.status,
                func.count().label("count"),
            )
            .where(
                IngestionDocumentStageStateModel.ingestion_job_id
                == ingestion_job_id,
            )
            .group_by(
                IngestionDocumentStageStateModel.stage,
                IngestionDocumentStageStateModel.status,
            )
        )

        result = await self.session.execute(statement)

        return [
            StageCount(
                stage=row.stage,
                status=row.status,
                count=row._mapping["count"],
            )
            for row in result.all()
        ]

    async def list_batch_stage_counts(
        self,
        *,
        ingestion_batch_id: UUID,
    ) -> list[StageCount]:

        statement = (
            select(
                IngestionDocumentStageStateModel.stage,
                IngestionDocumentStageStateModel.status,
                func.count().label("count"),
            )
            .where(
                IngestionDocumentStageStateModel.ingestion_batch_id
                == ingestion_batch_id,
            )
            .group_by(
                IngestionDocumentStageStateModel.stage,
                IngestionDocumentStageStateModel.status,
            )
        )

        result = await self.session.execute(statement)

        return [
            StageCount(
                stage=row.stage,
                status=row.status,
                count=row._mapping["count"],
            )
            for row in result.all()
        ]

    async def get_batch(
        self,
        *,
        ingestion_job_id: UUID,
        ingestion_batch_id: UUID,
    ) -> BatchSummary | None:

        model = await self.session.get(
            IngestionBatchModel,
            ingestion_batch_id,
        )

        if (
            model is None
            or model.ingestion_job_id != ingestion_job_id
        ):
            return None

        return BatchSummary(
            id=model.id,
            batch_index=model.batch_index,
            status=model.status,
            total_files=model.total_files,
            completed_files=model.completed_files,
            failed_files=model.failed_files,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_batch_documents(
        self,
        *,
        ingestion_job_id: UUID,
        ingestion_batch_id: UUID,
    ) -> list[BatchDocumentView]:

        statement = (
            select(
                IngestionBatchDocumentModel,
                DocumentModel,
            )
            .join(
                DocumentModel,
                DocumentModel.id
                == IngestionBatchDocumentModel.document_id,
            )
            .where(
                IngestionBatchDocumentModel.ingestion_job_id
                == ingestion_job_id,
                IngestionBatchDocumentModel.ingestion_batch_id
                == ingestion_batch_id,
            )
            .order_by(
                IngestionBatchDocumentModel.ordinal.asc()
            )
        )

        result = await self.session.execute(statement)
        rows = result.all()

        if not rows:
            return []

        states_statement = (
            select(IngestionDocumentStageStateModel)
            .where(
                IngestionDocumentStageStateModel.ingestion_job_id
                == ingestion_job_id,
                IngestionDocumentStageStateModel.ingestion_batch_id
                == ingestion_batch_id,
            )
            .order_by(
                IngestionDocumentStageStateModel.document_id.asc(),
                self._stage_order_expression(),
            )
        )

        states_result = await self.session.execute(
            states_statement,
        )
        states_by_document: dict[
            UUID,
            list[DocumentStageStateView],
        ] = {}

        for state in states_result.scalars().all():
            states_by_document.setdefault(
                state.document_id,
                [],
            ).append(
                DocumentStageStateView(
                    document_id=state.document_id,
                    stage=state.stage,
                    status=state.status,
                    started_at=state.started_at,
                    completed_at=state.completed_at,
                    error=state.error,
                )
            )

        return [
            BatchDocumentView(
                document_id=document.id,
                ordinal=membership.ordinal,
                file_name=document.file_name,
                file_extension=document.file_extension,
                file_size_bytes=document.file_size_bytes,
                stages=states_by_document.get(
                    document.id,
                    [],
                ),
            )
            for membership, document in rows
        ]

    async def list_document_stage_states(
        self,
        *,
        ingestion_job_id: UUID,
        document_id: UUID,
    ) -> list[DocumentStageStateView]:

        statement = (
            select(IngestionDocumentStageStateModel)
            .where(
                IngestionDocumentStageStateModel.ingestion_job_id
                == ingestion_job_id,
                IngestionDocumentStageStateModel.document_id
                == document_id,
            )
            .order_by(
                self._stage_order_expression(),
            )
        )

        result = await self.session.execute(statement)

        return [
            DocumentStageStateView(
                document_id=model.document_id,
                stage=model.stage,
                status=model.status,
                started_at=model.started_at,
                completed_at=model.completed_at,
                error=model.error,
            )
            for model in result.scalars().all()
        ]

    @staticmethod
    def _stage_order_expression():
        return case(
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.DISCOVERY.value,
                1,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.DOWNLOAD.value,
                2,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.EXTRACTION.value,
                3,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.CHUNKING.value,
                4,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.EMBEDDING.value,
                5,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.CLASSIFICATION.value,
                6,
            ),
            (
                IngestionDocumentStageStateModel.stage
                == IngestionStage.INDEXING.value,
                7,
            ),
            else_=99,
        )

    async def list_events_after(
        self,
        *,
        ingestion_job_id: UUID,
        after: int,
        limit: int = 100,
    ) -> list[OrchestrationEventView]:

        statement = (
            select(IngestionOrchestrationEventModel)
            .where(
                IngestionOrchestrationEventModel.ingestion_job_id
                == ingestion_job_id,
                IngestionOrchestrationEventModel.sequence_no
                > after,
            )
            .order_by(
                IngestionOrchestrationEventModel.sequence_no.asc(),
            )
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return [
            OrchestrationEventView(
                sequence_no=model.sequence_no,
                ingestion_job_id=model.ingestion_job_id,
                ingestion_batch_id=model.ingestion_batch_id,
                document_id=model.document_id,
                event_type=model.event_type,
                stage=model.stage,
                status=model.status,
                payload=model.payload,
                created_at=model.created_at,
            )
            for model in result.scalars().all()
        ]
