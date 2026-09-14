from datetime import datetime
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy import or_
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

    async def create(
        self,
        enterprise: Enterprise,
    ) -> Enterprise:

        model = EnterpriseModel(
            code=enterprise.code,
            name=enterprise.name,
            description=enterprise.description,
            status=enterprise.status,
        )

        self.session.add(
            model,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return EnterpriseMapper.to_entity(
            model,
        )

    async def update(
        self,
        enterprise: Enterprise,
    ) -> Enterprise:

        if enterprise.id is None:
            raise ValueError(
                "Enterprise id is required for update"
            )

        model = await self.session.get(
            EnterpriseModel,
            enterprise.id,
        )

        if model is None:
            raise ValueError(
                "Enterprise not found"
            )

        model.code = enterprise.code
        model.name = enterprise.name
        model.description = enterprise.description
        model.status = enterprise.status

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return EnterpriseMapper.to_entity(
            model,
        )

    async def list_page(
        self,
        *,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_id: UUID | None = None,
    ) -> list[Enterprise]:

        statement = select(
            EnterpriseModel,
        )

        if (
            cursor_created_at is not None
            and cursor_id is not None
        ):
            statement = statement.where(
                or_(
                    EnterpriseModel.created_at
                    < cursor_created_at,
                    and_(
                        EnterpriseModel.created_at
                        == cursor_created_at,
                        EnterpriseModel.id < cursor_id,
                    ),
                )
            )

        statement = (
            statement
            .order_by(
                EnterpriseModel.created_at.desc(),
                EnterpriseModel.id.desc(),
            )
            .limit(limit)
        )

        result = await self.session.execute(
            statement,
        )

        return [
            EnterpriseMapper.to_entity(model)
            for model in result.scalars().all()
        ]

    async def list_enabled(
        self,
    ) -> list[Enterprise]:

        result = await self.session.execute(
            select(
                EnterpriseModel,
            )
            .where(
                EnterpriseModel.status == "ACTIVE",
            )
            .order_by(
                EnterpriseModel.name.asc(),
                EnterpriseModel.code.asc(),
            )
        )

        return [
            EnterpriseMapper.to_entity(model)
            for model in result.scalars().all()
        ]
