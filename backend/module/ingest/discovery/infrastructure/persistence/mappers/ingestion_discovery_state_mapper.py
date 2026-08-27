from module.ingest.discovery.domain.entities.ingestion_discovery_state import (
    IngestionDiscoveryState,
)

from module.ingest.discovery.infrastructure.persistence.models.ingestion_discovery_state_model import (
    IngestionDiscoveryStateModel,
)


class IngestionDiscoveryStateMapper:

    @staticmethod
    def to_entity(
        model: IngestionDiscoveryStateModel,
    ) -> IngestionDiscoveryState:

        return IngestionDiscoveryState(
            ingestion_job_id=(
                model.ingestion_job_id
            ),
            cursor=model.cursor,
            completed=model.completed,
            discovered_files=(
                model.discovered_files
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )