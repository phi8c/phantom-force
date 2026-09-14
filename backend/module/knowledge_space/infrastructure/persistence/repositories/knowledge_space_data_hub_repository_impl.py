from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.domain.contracts.knowledge_space_data_hub_repository import (
    KnowledgeSpaceDataHubRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)
from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_data_hub_mapper import (
    KnowledgeSpaceDataHubMapper,
)
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_data_hub_model import (
    KnowledgeSpaceDataHubModel,
)


class KnowledgeSpaceDataHubRepositoryImpl(
    KnowledgeSpaceDataHubRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHub | None:

        result = await self.session.execute(
            select(
                KnowledgeSpaceDataHubModel,
            ).where(
                KnowledgeSpaceDataHubModel.knowledge_space_id
                == knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return KnowledgeSpaceDataHubMapper.to_entity(
            model,
        )

    async def upsert(
        self,
        config: KnowledgeSpaceDataHub,
    ) -> KnowledgeSpaceDataHub:

        result = await self.session.execute(
            select(
                KnowledgeSpaceDataHubModel,
            ).where(
                KnowledgeSpaceDataHubModel.knowledge_space_id
                == config.knowledge_space_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            model = KnowledgeSpaceDataHubModel(
                knowledge_space_id=config.knowledge_space_id,
                data_hub_provider_id=(
                    config.data_hub_provider_id
                ),
                configuration=config.configuration,
                enabled=config.enabled,
            )
            self.session.add(
                model,
            )
        else:
            model.data_hub_provider_id = (
                config.data_hub_provider_id
            )
            model.configuration = config.configuration
            model.enabled = config.enabled

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return KnowledgeSpaceDataHubMapper.to_entity(
            model,
        )
