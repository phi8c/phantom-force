from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.knowledge.application.services.knowledge_writer import (
    KnowledgeWriter,
)
from module.ingest.knowledge.infrastructure.persistence.repositories.knowledge_repository_impl import (
    KnowledgeRepositoryImpl,
)


def create_knowledge_writer(
    session: AsyncSession,
) -> KnowledgeWriter:

    return KnowledgeWriter(
        repository=KnowledgeRepositoryImpl(
            session=session,
        ),
    )
