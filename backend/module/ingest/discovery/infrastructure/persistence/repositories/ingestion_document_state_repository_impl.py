from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.discovery.domain.entities.ingestion_document_state import (
    IngestionDocumentState,
)

from module.ingest.discovery.domain.contracts.ingestion_document_state_repository import (
    IngestionDocumentStateRepository,
)

from module.ingest.discovery.infrastructure.persistence.mappers.ingestion_document_state_mapper import (
    IngestionDocumentStateMapper,
)

from module.ingest.discovery.infrastructure.persistence.models.ingestion_document_state_model import (
    IngestionDocumentStateModel,
)


class IngestionDocumentStateRepositoryImpl(
    IngestionDocumentStateRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_document_and_ingestion_job(
        self,
        document_id: UUID,
        ingestion_job_id: UUID,
    ) -> IngestionDocumentState | None:

        statement = select(
            IngestionDocumentStateModel
        ).where(
            IngestionDocumentStateModel.document_id
            == document_id,
            IngestionDocumentStateModel.ingestion_job_id
            == ingestion_job_id,
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if not model:
            return None

        return IngestionDocumentStateMapper.to_entity(
            model,
        )

    async def create(
        self,
        state: IngestionDocumentState,
    ) -> IngestionDocumentState:

        model = IngestionDocumentStateMapper.to_model(
            state,
        )

        self.session.add(
            model,
        )

        await self.session.flush()

        return IngestionDocumentStateMapper.to_entity(
            model,
        )

    async def update(
        self,
        state: IngestionDocumentState,
    ) -> IngestionDocumentState:

        model = await self.session.get(
            IngestionDocumentStateModel,
            (
                state.document_id,
                state.ingestion_job_id,
            ),
        )

        if not model:
            raise ValueError(
                "IngestionDocumentState not found"
            )

        model.status = (
            state.status.value
        )

        model.updated_at = datetime.now(
            timezone.utc,
        )

        await self.session.flush()

        return IngestionDocumentStateMapper.to_entity(
            model,
        )