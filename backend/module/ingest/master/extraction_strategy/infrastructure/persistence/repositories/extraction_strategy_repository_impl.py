from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.extraction_strategy.domain.contracts.extraction_strategy_repository import (
    ExtractionStrategyRepository,
)
from module.ingest.master.extraction_strategy.domain.entities.extraction_strategy import (
    ExtractionStrategy,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.mappers.extraction_strategy_mapper import (
    ExtractionStrategyMapper,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.models.extraction_strategy_model import (
    ExtractionStrategyModel,
)


class ExtractionStrategyRepositoryImpl(
    ExtractionStrategyRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        strategy_id: UUID,
    ) -> ExtractionStrategy | None:

        result = await self.session.execute(
            select(
                ExtractionStrategyModel,
            ).where(
                ExtractionStrategyModel.id
                == strategy_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ExtractionStrategyMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> ExtractionStrategy | None:

        result = await self.session.execute(
            select(
                ExtractionStrategyModel,
            ).where(
                ExtractionStrategyModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ExtractionStrategyMapper.to_entity(
            model,
        )