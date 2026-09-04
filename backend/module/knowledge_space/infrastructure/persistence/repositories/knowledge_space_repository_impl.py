from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
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

