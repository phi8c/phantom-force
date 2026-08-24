from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.config.application.services.ingestion_config_service import (
    IngestionConfigService,
)
from module.ingest.config.application.use_cases.get_ingestion_config import (
    GetIngestionConfigUseCase,
)
from module.ingest.config.application.use_cases.get_ingestion_job import (
    GetIngestionJobUseCase,
)
from module.ingest.config.application.use_cases.get_ingestion_job_configuration import (
    GetIngestionJobConfigurationUseCase,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)


def create_ingestion_config_service(
    session: AsyncSession,
) -> IngestionConfigService:

    repository = IngestionConfigRepositoryImpl(
        session=session,
    )

    get_job = GetIngestionJobUseCase(
        repository=repository,
    )

    get_configuration = (
        GetIngestionJobConfigurationUseCase(
            repository=repository,
        )
    )

    get_config = GetIngestionConfigUseCase(
        repository=repository,
    )

    return IngestionConfigService(
        get_job=get_job,
        get_configuration=get_configuration,
        get_config=get_config,
    )