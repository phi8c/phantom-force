from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.application.services.knowledge_space_service import (
    KnowledgeSpaceService,
)
from module.knowledge_space.application.use_cases.get_data_hub_config import (
    GetKnowledgeSpaceDataHubUseCase,
)
from module.knowledge_space.application.use_cases.get_embedding_config import (
    GetKnowledgeSpaceEmbeddingConfigUseCase,
)
from module.knowledge_space.application.use_cases.get_knowledge_space import (
    GetKnowledgeSpaceUseCase,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_repository_impl import (
    KnowledgeSpaceRepositoryImpl,
)


def create_knowledge_space(
    session: AsyncSession,
) -> KnowledgeSpaceService:

    repository = KnowledgeSpaceRepositoryImpl(
        session=session,
    )

    get_knowledge_space = (
        GetKnowledgeSpaceUseCase(
            repository=repository,
        )
    )

    get_data_hub_config = (
        GetKnowledgeSpaceDataHubUseCase(
            repository=repository,
        )
    )

    get_embedding_config = (
        GetKnowledgeSpaceEmbeddingConfigUseCase(
            repository=repository,
        )
    )

    return KnowledgeSpaceService(
        get_knowledge_space=get_knowledge_space,
        get_data_hub_config=get_data_hub_config,
        get_embedding_config=get_embedding_config,
    )