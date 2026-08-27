from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.discovery.domain.contracts.ingestion_discovery_state_repository import (
    IngestionDiscoveryStateRepository,
)

from module.ingest.discovery.domain.entities.ingestion_discovery_state import (
    IngestionDiscoveryState,
)

from module.ingest.discovery.infrastructure.persistence.mappers.ingestion_discovery_state_mapper import (
    IngestionDiscoveryStateMapper,
)

from module.ingest.discovery.infrastructure.persistence.models.ingestion_discovery_state_model import (
    IngestionDiscoveryStateModel,
)


class IngestionDiscoveryStateRepositoryImpl(
    IngestionDiscoveryStateRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_ingestion_job_id(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionDiscoveryState | None:

        statement = select(
            IngestionDiscoveryStateModel
        ).where(
            IngestionDiscoveryStateModel.ingestion_job_id
            == ingestion_job_id
        )

        result = await self.session.execute(
            statement,
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return IngestionDiscoveryStateMapper.to_entity(
            model,
        )

    async def save_progress(
        self,
        ingestion_job_id: UUID,
        cursor: dict | None,
        discovered_count: int,
        completed: bool,
    ) -> IngestionDiscoveryState:

        model = await self.session.get(
            IngestionDiscoveryStateModel,
            ingestion_job_id,
        )

        now = datetime.now(
            timezone.utc,
        )

        if model is None:
            model = IngestionDiscoveryStateModel(
                ingestion_job_id=(
                    ingestion_job_id
                ),
                cursor=cursor,
                completed=completed,
                discovered_files=(
                    discovered_count
                ),
                updated_at=now,
            )

            self.session.add(
                model,
            )

        else:
            model.cursor = cursor

            model.completed = completed

            model.discovered_files = (
                model.discovered_files
                + discovered_count
            )

            model.updated_at = now

        await self.session.flush()

        return IngestionDiscoveryStateMapper.to_entity(
            model,
        )

    async def complete(
        self,
        ingestion_job_id: UUID,
    ) -> IngestionDiscoveryState:

        model = await self.session.get(
            IngestionDiscoveryStateModel,
            ingestion_job_id,
        )

        now = datetime.now(
            timezone.utc,
        )

        if model is None:
            model = IngestionDiscoveryStateModel(
                ingestion_job_id=(
                    ingestion_job_id
                ),
                cursor=None,
                completed=True,
                discovered_files=0,
                updated_at=now,
            )

            self.session.add(
                model,
            )

        else:
            model.cursor = None
            model.completed = True
            model.updated_at = now

        await self.session.flush()

        return IngestionDiscoveryStateMapper.to_entity(
            model,
        )