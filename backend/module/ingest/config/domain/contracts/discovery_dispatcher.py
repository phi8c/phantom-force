from typing import Protocol
from uuid import UUID


class DiscoveryDispatcher(
    Protocol,
):

    async def dispatch(
        self,
        *,
        ingestion_job_id: UUID,
        batch_size: int,
    ) -> None:
        ...
