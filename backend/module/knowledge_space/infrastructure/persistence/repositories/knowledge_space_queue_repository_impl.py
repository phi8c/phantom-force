from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.domain.contracts.knowledge_space_queue_repository import (
    KnowledgeSpaceQueueRepository,
)
from module.knowledge_space.domain.entities.knowledge_space_queue import (
    KnowledgeSpaceQueue,
)
from module.knowledge_space.infrastructure.persistence.mappers.knowledge_space_queue_mapper import (
    KnowledgeSpaceQueueMapper,
)
from module.knowledge_space.infrastructure.persistence.models.knowledge_space_queue_model import (
    KnowledgeSpaceQueueModel,
)
from module.knowledge_space.infrastructure.persistence.models.queue_provider_model import (
    QueueProviderModel,
)


class KnowledgeSpaceQueueRepositoryImpl(KnowledgeSpaceQueueRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_default_for_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceQueue | None:
        result = await self._session.execute(
            select(
                KnowledgeSpaceQueueModel,
                QueueProviderModel,
            )
            .outerjoin(
                QueueProviderModel,
                QueueProviderModel.id
                == KnowledgeSpaceQueueModel.queue_provider_id,
            )
            .where(
                KnowledgeSpaceQueueModel.knowledge_space_id
                == knowledge_space_id,
                KnowledgeSpaceQueueModel.is_default.is_(True),
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        mapping, provider = row
        return KnowledgeSpaceQueueMapper.to_entity(
            mapping,
            provider,
        )
