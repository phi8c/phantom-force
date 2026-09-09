from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.embedding.composition import (
    create_text_embedding_provider,
)
from module.ingest.knowledge.application.services.knowledge_embedding_service import (
    KnowledgeEmbeddingService,
)
from module.ingest.knowledge.application.services.knowledge_reader import (
    KnowledgeReader,
)
from module.ingest.knowledge.application.services.knowledge_writer import (
    KnowledgeWriter,
)
from module.ingest.knowledge.infrastructure.persistence.repositories.knowledge_repository_impl import (
    KnowledgeRepositoryImpl,
)


def create_knowledge_writer(
    session: AsyncSession,
) -> KnowledgeWriter:

    repository = KnowledgeRepositoryImpl(
        session=session,
    )
    return KnowledgeWriter(
        repository=repository,
        embedding_service=KnowledgeEmbeddingService(
            repository=repository,
            embedder_factory=lambda knowledge_space_id: (
                create_text_embedding_provider(
                    session=session,
                    knowledge_space_id=knowledge_space_id,
                )
            ),
        ),
    )


def create_knowledge_reader(
    session: AsyncSession,
) -> KnowledgeReader:

    repository = KnowledgeRepositoryImpl(
        session=session,
    )
    return KnowledgeReader(
        repository=repository,
        embedder_factory=lambda knowledge_space_id: (
            create_text_embedding_provider(
                session=session,
                knowledge_space_id=knowledge_space_id,
            )
        ),
    )
