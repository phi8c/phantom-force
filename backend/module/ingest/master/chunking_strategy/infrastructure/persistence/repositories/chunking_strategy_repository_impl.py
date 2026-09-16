from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.chunking_strategy.domain.contracts.chunking_strategy_repository import (
    ChunkingStrategyRepository,
)
from module.ingest.master.chunking_strategy.domain.entities.chunking_strategy import (
    ChunkingStrategy,
)
from module.ingest.master.chunking_strategy.infrastructure.persistence.mappers.chunking_strategy_mapper import (
    ChunkingStrategyMapper,
)
from module.ingest.master.chunking_strategy.infrastructure.persistence.models.chunking_strategy_model import (
    ChunkingStrategyModel,
)


class ChunkingStrategyRepositoryImpl(
    ChunkingStrategyRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ChunkingStrategy | None:

        result = await self.session.execute(
            select(
                ChunkingStrategyModel,
            ).where(
                ChunkingStrategyModel.id
                == strategy_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ChunkingStrategyMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> ChunkingStrategy | None:

        result = await self.session.execute(
            select(
                ChunkingStrategyModel,
            ).where(
                func.upper(
                    ChunkingStrategyModel.code,
                )
                == code.strip().upper(),
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ChunkingStrategyMapper.to_entity(
            model,
        )

    async def list_enabled(
        self,
    ) -> list[ChunkingStrategy]:

        result = await self.session.execute(
            select(
                ChunkingStrategyModel,
            )
            .where(
                ChunkingStrategyModel.enabled.is_(True),
            )
            .order_by(
                ChunkingStrategyModel.name.asc(),
                ChunkingStrategyModel.code.asc(),
            )
        )

        return [
            ChunkingStrategyMapper.to_entity(model)
            for model in result.scalars().all()
        ]
