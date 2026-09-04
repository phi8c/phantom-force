from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.master.model_set.domain.contracts.model_set_repository import (
    ModelSetRepository,
)
from module.ingest.master.model_set.domain.entities.model_set import (
    ModelSet,
)
from module.ingest.master.model_set.infrastructure.persistence.mappers.model_set_mapper import (
    ModelSetMapper,
)
from module.ingest.master.model_set.infrastructure.persistence.models.model_set_model import (
    ModelSetModel,
)


class ModelSetRepositoryImpl(
    ModelSetRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        model_set_id: UUID,
    ) -> ModelSet | None:

        result = await self.session.execute(
            select(
                ModelSetModel,
            ).where(
                ModelSetModel.id == model_set_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ModelSetMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> ModelSet | None:

        result = await self.session.execute(
            select(
                ModelSetModel,
            ).where(
                func.upper(ModelSetModel.code)
                == code.strip().upper(),
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return ModelSetMapper.to_entity(
            model,
        )
