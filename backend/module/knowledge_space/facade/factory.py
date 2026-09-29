from sqlalchemy.ext.asyncio import AsyncSession

from module.knowledge_space.facade.contract import KnowledgeSpaceModuleFacade
from module.knowledge_space.facade.local_facade import LocalKnowledgeSpaceFacade
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_repository_impl import (
    KnowledgeSpaceRepositoryImpl,
)


def get_knowledge_space_facade(
    session: AsyncSession,
) -> KnowledgeSpaceModuleFacade:
    return LocalKnowledgeSpaceFacade(
        repository=KnowledgeSpaceRepositoryImpl(session=session),
    )
