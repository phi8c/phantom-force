from uuid import UUID

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.enterprise.infrastructure.persistence.models.enterprise_model import (
    EnterpriseModel,
)
from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)
from module.knowledge_space.domain.entities.knowledge_space_list_item import (
    KnowledgeSpaceListItem,
)

from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_mapper import (
    KnowledgeSpaceMapper,
)

from module.knowledge_space.infrastructure.persistence.models.knowledge_space_model import (
    KnowledgeSpaceModel,
)


class KnowledgeSpaceRepositoryImpl(
    KnowledgeSpaceRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpace | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceModel,
            ).where(
                KnowledgeSpaceModel.id
                == knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return KnowledgeSpaceMapper.to_entity(
            model,
        )

    async def create(
        self,
        knowledge_space: KnowledgeSpace,
    ) -> KnowledgeSpace:

        model = KnowledgeSpaceModel(
            enterprise_id=knowledge_space.enterprise_id,
            name=knowledge_space.name,
            code=knowledge_space.code,
            description=knowledge_space.description,
            status=knowledge_space.status,
            configuration=knowledge_space.configuration,
        )

        self.session.add(
            model,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return KnowledgeSpaceMapper.to_entity(
            model,
        )

    async def list_page(
        self,
        *,
        limit: int,
        offset: int,
        enterprise_id: UUID | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[list[KnowledgeSpaceListItem], int]:

        filters = []

        if enterprise_id is not None:
            filters.append(
                KnowledgeSpaceModel.enterprise_id
                == enterprise_id,
            )

        if status is not None:
            filters.append(
                KnowledgeSpaceModel.status == status,
            )

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    KnowledgeSpaceModel.name.ilike(
                        search_pattern,
                    ),
                    KnowledgeSpaceModel.code.ilike(
                        search_pattern,
                    ),
                )
            )

        total_statement = (
            select(
                func.count(),
            )
            .select_from(
                KnowledgeSpaceModel,
            )
            .join(
                EnterpriseModel,
                EnterpriseModel.id
                == KnowledgeSpaceModel.enterprise_id,
            )
        )

        list_statement = (
            select(
                KnowledgeSpaceModel,
                EnterpriseModel.name.label(
                    "enterprise_name",
                ),
            )
            .join(
                EnterpriseModel,
                EnterpriseModel.id
                == KnowledgeSpaceModel.enterprise_id,
            )
            .order_by(
                KnowledgeSpaceModel.created_at.desc(),
                KnowledgeSpaceModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        if filters:
            total_statement = total_statement.where(
                *filters,
            )
            list_statement = list_statement.where(
                *filters,
            )

        total_result = await self.session.execute(
            total_statement,
        )
        total = int(
            total_result.scalar_one(),
        )

        rows = await self.session.execute(
            list_statement,
        )

        items = [
            KnowledgeSpaceListItem(
                id=model.id,
                enterprise_id=model.enterprise_id,
                enterprise_name=enterprise_name,
                name=model.name,
                code=model.code,
                description=model.description,
                status=model.status,
                created_at=model.created_at,
            )
            for model, enterprise_name in rows.all()
        ]

        return (
            items,
            total,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> KnowledgeSpace | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceModel,
            ).where(
                KnowledgeSpaceModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return KnowledgeSpaceMapper.to_entity(
            model,
        )

