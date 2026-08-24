from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.ingestion_source import (
    IngestionSource,
)
from app.domain.repositories.source_repository import (
    SourceRepository,
)

from app.infrastructure.persistence.mappers.ingestion_source_mapper import (
    IngestionSourceMapper,
)

from app.infrastructure.persistence.models.ingestion_source_model import (
    IngestionSourceModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class SourceRepositoryImpl(
    BaseRepository[IngestionSourceModel],
    SourceRepository,
):
    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=IngestionSourceModel,
        )

    async def get_by_id(
        self,
        source_id: UUID,
    ) -> IngestionSource | None:

        model = await super().get_by_id(
            source_id,
        )

        if not model:
            return None

        return (
            IngestionSourceMapper.to_entity(
                model,
            )
        )

    async def get_enabled_sources(
        self,
    ) -> list[IngestionSource]:

        result = await self.session.execute(
            select(
                IngestionSourceModel,
            ).where(
                IngestionSourceModel.enabled.is_(True),
            ),
        )

        return [
            IngestionSourceMapper.to_entity(
                model,
            )
            for model in result.scalars().all()
        ]

    async def create(
        self,
        source: IngestionSource,
    ) -> IngestionSource:

        model = (
            IngestionSourceMapper.to_model(
                source,
            )
        )

        model = await self.add(
            model,
        )

        return (
            IngestionSourceMapper.to_entity(
                model,
            )
        )

    async def update(
        self,
        source: IngestionSource,
    ) -> None:

        model = (
            await super().get_by_id(
                source.id,
            )
        )

        if not model:
            raise ValueError(
                "Source not found",
            )

        model.name = source.name
        model.site_id = source.site_id
        model.drive_id = source.drive_id
        model.enabled = source.enabled

        await self.session.flush()