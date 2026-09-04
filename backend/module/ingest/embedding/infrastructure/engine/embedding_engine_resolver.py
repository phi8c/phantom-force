from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.embedding.infrastructure.engine.legacy_embedding_engine import (
    LegacyEmbeddingEngineAdapter,
)
from module.ai.embedding_model.infrastructure.persistence.repositories.embedding_model_repository_impl import (
    EmbeddingModelRepositoryImpl,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.embedding.domain.contracts.embedding_engine import (
    EmbeddingEngine,
)
from module.ingest.embedding.domain.contracts.embedding_engine_resolver import (
    EmbeddingEngineResolver,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_embedding_config_repository_impl import (
    KnowledgeSpaceEmbeddingConfigRepositoryImpl,
)


class DbEmbeddingEngineResolver(
    EmbeddingEngineResolver,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._ingestion_config_repository = (
            IngestionConfigRepositoryImpl(
                session,
            )
        )
        self._embedding_config_repository = (
            KnowledgeSpaceEmbeddingConfigRepositoryImpl(
                session,
            )
        )
        self._embedding_model_repository = (
            EmbeddingModelRepositoryImpl(
                session,
            )
        )

    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> EmbeddingEngine:

        job = await self._ingestion_config_repository.get_job_by_id(
            ingestion_job_id,
        )

        if job is None:
            raise ValueError(
                "Ingestion job is not available"
            )

        embedding_config = (
            await self._embedding_config_repository
            .get_by_knowledge_space_id(
                job.knowledge_space_id,
            )
        )

        if (
            embedding_config is None
            or not embedding_config.enabled
        ):
            raise ValueError(
                "Embedding configuration is not available "
                "for this ingestion job"
            )

        embedding_model = (
            await self._embedding_model_repository
            .get_by_id(
                embedding_config.embedding_model_id,
            )
        )

        if (
            embedding_model is None
            or not embedding_model.enabled
        ):
            raise ValueError(
                "Embedding model is not available "
                "or disabled"
            )

        configuration = {
            **(
                embedding_model.configuration
                or {}
            ),
            **(
                embedding_config.configuration
                or {}
            ),
        }

        return self._create_engine(
            code=embedding_model.code,
            provider=embedding_model.provider,
            model_name=configuration.get(
                "model_name",
                embedding_model.code,
            ),
            deployment=configuration.get(
                "deployment",
            )
            or configuration.get(
                "deployment_name",
            )
            or configuration.get(
                "azure_deployment",
            )
            or embedding_model.code,
        )

    def _create_engine(
        self,
        *,
        code: str,
        provider: str,
        model_name: str,
        deployment: str,
    ) -> EmbeddingEngine:

        normalized_provider = provider.strip().lower()

        if normalized_provider in {
            "azure",
            "azure_openai",
            "azure-openai",
            "openai",
        }:
            return LegacyEmbeddingEngineAdapter(
                deployment=deployment,
                model_name=model_name or code,
            )

        raise ValueError(
            "Unsupported embedding provider: "
            f"{provider}"
        )
