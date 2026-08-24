from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.enterprise.domain.contracts.enterprise_repository import (
    EnterpriseRepository,
)
from module.enterprise.domain.entities.enterprise import (
    Enterprise,
)

from module.enterprise.infrastructure.persistence.mappers.enterprise_mapper import (
    EnterpriseMapper,
)

from module.enterprise.infrastructure.persistence.models.enterprise_model import (
    EnterpriseModel,
)


class EnterpriseRepositoryImpl(
    EnterpriseRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        enterprise_id: UUID,
    ) -> Enterprise | None:

        result = await self.session.execute(
            select(
                EnterpriseModel,
            ).where(
                EnterpriseModel.id
                == enterprise_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return EnterpriseMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> Enterprise | None:

        result = await self.session.execute(
            select(
                EnterpriseModel,
            ).where(
                EnterpriseModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return EnterpriseMapper.to_entity(
            model,
        )