from __future__ import annotations

from module.ingest.config.application.dtos.list_ingestion_jobs import (
    IngestionJobListItem,
)
from module.ingest.config.application.dtos.list_ingestion_jobs import (
    ListIngestionJobsQuery,
)
from module.ingest.config.application.dtos.list_ingestion_jobs import (
    ListIngestionJobsResult,
)
from module.ingest.config.domain.contracts.ingestion_config_repository import (
    IngestionConfigRepository,
)


class ListIngestionJobsUseCase:
    def __init__(
        self,
        repository: IngestionConfigRepository,
    ) -> None:
        self._repository = repository

    async def execute(
        self,
        query: ListIngestionJobsQuery,
    ) -> ListIngestionJobsResult:
        if query.limit <= 0 or query.limit > 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        page = await self._repository.list_jobs(
            knowledge_space_id=query.knowledge_space_id,
            status=query.status,
            limit=query.limit,
            cursor=query.cursor,
        )

        return ListIngestionJobsResult(
            items=[
                IngestionJobListItem(
                    id=job.id,
                    knowledge_space_id=job.knowledge_space_id,
                    trigger_type=job.trigger_type,
                    status=job.status,
                    is_build_graph=job.is_build_graph,
                    total_files=job.total_files,
                    completed_files=job.completed_files,
                    failed_files=job.failed_files,
                    started_at=job.started_at,
                    finished_at=job.finished_at,
                    created_at=job.created_at,
                    scope_type=job.scope_type,
                    scope_data=job.scope_data,
                )
                for job in page.items
                if job.id is not None
            ],
            next_cursor=page.next_cursor,
            has_more=page.has_more,
        )
