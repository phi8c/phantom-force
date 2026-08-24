from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.sync_state import (
    SyncState,
)

from app.domain.repositories.sync_state_repository import (
    SyncStateRepository,
)

from app.infrastructure.database.mappers.sync_state_mapper import (
    SyncStateMapper,
)

from app.infrastructure.database.models.sync_state_model import (
    SyncStateModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class SyncStateRepositoryImpl(
    BaseRepository[SyncStateModel],
    SyncStateRepository,
):
    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=SyncStateModel,
        )

    async def get_by_source_id(
        self,
        source_id: UUID,
    ) -> SyncState | None:

        result = await self.session.execute(
            select(
                SyncStateModel,
            ).where(
                SyncStateModel.source_id
                == source_id,
            ),
        )

        model = result.scalar_one_or_none()

        if not model:
            return None

        return SyncStateMapper.to_entity(
            model,
        )

    async def create(
        self,
        sync_state: SyncState,
    ) -> SyncState:

        model = SyncStateMapper.to_model(
            sync_state,
        )

        created_model = await self.add(
            model,
        )

        return SyncStateMapper.to_entity(
            created_model,
        )

    async def update(
        self,
        sync_state: SyncState,
    ) -> None:

        model = await super().get_by_id(
            sync_state.id,
        )

        if not model:
            raise ValueError(
                "Sync state not found",
            )

        model.delta_token = (
            sync_state.delta_token
        )

        model.last_sync_at = (
            sync_state.last_sync_at
        )

        await self.session.flush()