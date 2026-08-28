from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from integration.ingest.embedding.legacy_embedding_engine import (
    LegacyEmbeddingEngineAdapter,
)
from module.ingest.embedding.domain.contracts.embedding_engine import (
    EmbeddingEngine,
)
from module.ingest.embedding.domain.contracts.embedding_engine_resolver import (
    EmbeddingEngineResolver,
)


class DbEmbeddingEngineResolver(
    EmbeddingEngineResolver,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session

    async def resolve_for_job(
        self,
        ingestion_job_id: UUID,
    ) -> EmbeddingEngine:

        result = await self._session.execute(
            text(
                """
                SELECT
                    embedding_models.code,
                    embedding_models.name,
                    embedding_models.provider,
                    embedding_models.dimension,
                    embedding_models.configuration
                        AS model_configuration,
                    knowledge_space_embedding_configs.configuration
                        AS embedding_configuration
                FROM ingestion_jobs
                JOIN knowledge_space_embedding_configs
                  ON knowledge_space_embedding_configs.knowledge_space_id
                   = ingestion_jobs.knowledge_space_id
                JOIN embedding_models
                  ON embedding_models.id
                   = knowledge_space_embedding_configs.embedding_model_id
                WHERE ingestion_jobs.id = :ingestion_job_id
                  AND knowledge_space_embedding_configs.enabled = true
                  AND embedding_models.enabled = true
                LIMIT 1
                """
            ),
            {
                "ingestion_job_id": ingestion_job_id,
            },
        )

        row = result.mappings().one_or_none()

        if row is None:
            raise ValueError(
                "Embedding configuration is not available "
                "for this ingestion job"
            )

        configuration = {
            **(
                row["model_configuration"]
                or {}
            ),
            **(
                row["embedding_configuration"]
                or {}
            ),
        }

        return self._create_engine(
            code=row["code"],
            provider=row["provider"],
            model_name=configuration.get(
                "model_name",
                row["code"],
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
            or row["code"],
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
