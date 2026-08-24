from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.sync_state import (
    SyncState,
)


class SyncStateRepository(
    ABC,
):

    @abstractmethod
    async def get_by_source_id(
        self,
        source_id: UUID,
    ) -> SyncState | None:
        pass

    @abstractmethod
    async def create(
        self,
        sync_state: SyncState,
    ) -> SyncState:
        pass

    @abstractmethod
    async def update(
        self,
        sync_state: SyncState,
    ) -> None:
        pass