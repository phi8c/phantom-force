from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.orchestration.application.services import (
    OrchestrationProgressService,
)
from module.ingest.orchestration.infrastructure.persistence.queries import (
    OrchestrationQueryService,
)
from module.ingest.orchestration.infrastructure.persistence.repositories import (
    OrchestrationRepositoryImpl,
)


def create_orchestration_progress_service(
    session: AsyncSession,
) -> OrchestrationProgressService:

    return OrchestrationProgressService(
        repository=OrchestrationRepositoryImpl(
            session=session,
        ),
    )


def create_orchestration_query_service(
    session: AsyncSession,
) -> OrchestrationQueryService:

    return OrchestrationQueryService(
        session=session,
    )
