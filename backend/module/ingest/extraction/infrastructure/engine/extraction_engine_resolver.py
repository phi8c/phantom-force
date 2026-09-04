from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.extraction.infrastructure.engine.docling_extraction_engine import (
    DoclingExtractionEngine,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.extraction.domain.contracts.extraction_engine import (
    ExtractionEngine,
)
from module.ingest.extraction.domain.contracts.extraction_engine_resolver import (
    ExtractionEngineResolver,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.repositories.extraction_strategy_repository_impl import (
    ExtractionStrategyRepositoryImpl,
)


class DbExtractionEngineResolver(
    ExtractionEngineResolver,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._configuration_repository = (
            IngestionConfigRepositoryImpl(
                session=session,
            )
        )
        self._extraction_repository = (
            ExtractionStrategyRepositoryImpl(
                session=session,
            )
        )

    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> ExtractionEngine:

        configuration = (
            await self._configuration_repository
            .get_configuration_by_job_id(
                ingestion_job_id,
            )
        )

        if configuration is None:
            raise ValueError(
                "Ingestion job configuration not found"
            )

        extraction_engine = (
            await self._extraction_repository
            .get_by_id(
                configuration.extraction_engine_id,
            )
        )

        if (
            extraction_engine is None
            or not extraction_engine.enabled
        ):
            raise ValueError(
                "Extraction engine is not available "
                "or disabled"
            )

        return self._create_engine(
            code=extraction_engine.code,
            provider=extraction_engine.provider,
            configuration={
                **(
                    extraction_engine.configuration
                    or {}
                ),
                **(
                    configuration.configuration
                    or {}
                ),
            },
        )

    def _create_engine(
        self,
        *,
        code: str,
        provider: str,
        configuration: dict,
    ) -> ExtractionEngine:

        normalized_code = code.strip().upper()
        normalized_provider = provider.strip().lower()

        if (
            normalized_code == "DOCLING"
            or normalized_provider == "docling"
        ):
            return DoclingExtractionEngine()

        raise ValueError(
            "Unsupported extraction engine: "
            f"{code}"
        )
