from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.chunking_strategy.infrastructure.persistence.repositories.chunking_strategy_repository_impl import (
    ChunkingStrategyRepositoryImpl,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.repositories.extraction_strategy_repository_impl import (
    ExtractionStrategyRepositoryImpl,
)


@dataclass(frozen=True)
class IngestionMasterConfig:
    extraction_engine_id: UUID
    chunking_strategy_id: UUID
    model_set_id: UUID | None


class IngestionMasterConfigResolver:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self._session = session
        self._extraction_repository = (
            ExtractionStrategyRepositoryImpl(
                session=session,
            )
        )
        self._chunking_repository = (
            ChunkingStrategyRepositoryImpl(
                session=session,
            )
        )

    async def resolve(
        self,
        *,
        extraction_engine_code: str,
        chunking_strategy_code: str,
        model_set_code: str | None = None,
    ) -> IngestionMasterConfig:

        extraction_engine = (
            await self._extraction_repository
            .get_by_code(
                self._normalize_code(
                    extraction_engine_code,
                )
            )
        )

        if (
            extraction_engine is None
            or extraction_engine.id is None
            or not extraction_engine.enabled
        ):
            raise ValueError(
                "extraction_engine_code is not "
                "available or disabled"
            )

        chunking_strategy = (
            await self._chunking_repository
            .get_by_code(
                self._normalize_code(
                    chunking_strategy_code,
                )
            )
        )

        if (
            chunking_strategy is None
            or chunking_strategy.id is None
            or not chunking_strategy.enabled
        ):
            raise ValueError(
                "chunking_strategy_code is not "
                "available or disabled"
            )

        model_set_id = await self._resolve_model_set_id(
            model_set_code,
        )

        return IngestionMasterConfig(
            extraction_engine_id=extraction_engine.id,
            chunking_strategy_id=chunking_strategy.id,
            model_set_id=model_set_id,
        )

    async def _resolve_model_set_id(
        self,
        code: str | None,
    ) -> UUID | None:

        if not code:
            return None

        result = await self._session.execute(
            text(
                """
                SELECT id
                FROM model_sets
                WHERE upper(code) = upper(:code)
                  AND enabled = true
                LIMIT 1
                """
            ),
            {
                "code": self._normalize_code(
                    code,
                ),
            },
        )

        row = result.mappings().one_or_none()

        if row is None:
            raise ValueError(
                "model_set_code is not available "
                "or disabled"
            )

        return row["id"]

    @staticmethod
    def _normalize_code(
        code: str,
    ) -> str:

        normalized = code.strip().upper()

        if not normalized:
            raise ValueError(
                "code must not be empty"
            )

        return normalized
