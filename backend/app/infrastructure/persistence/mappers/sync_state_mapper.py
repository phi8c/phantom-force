from app.domain.entities.sync_state import (
    SyncState,
)

from app.infrastructure.persistence.models.sync_state_model import (
    SyncStateModel,
)


class SyncStateMapper:

    @staticmethod
    def to_entity(
        model: SyncStateModel,
    ) -> SyncState:

        return SyncState(
            id=model.id,
            source_id=model.source_id,
            delta_token=model.delta_token,
            last_sync_at=model.last_sync_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: SyncState,
    ) -> SyncStateModel:

        return SyncStateModel(
            id=entity.id,
            source_id=entity.source_id,
            delta_token=entity.delta_token,
            last_sync_at=entity.last_sync_at,
        )