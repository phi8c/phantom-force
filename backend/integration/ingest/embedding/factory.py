from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.embedding.application.use_cases.embed_batch import (
    EmbedBatchUseCase,
)
from module.ingest.embedding.infrastructure.persistence.repositories.document_chunk_embedding_repository_impl import (
    DocumentChunkEmbeddingRepositoryImpl,
)
from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import (
    EmbeddingTaskRepositoryImpl,
)
from module.ingest.embedding.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)

from integration.ingest.embedding.batch_finalizer import (
    ModuleBatchFinalizer,
)
from integration.ingest.embedding.chunk_reader import (
    ModuleChunkReader,
)
from integration.ingest.embedding.legacy_embedding_engine import (
    LegacyEmbeddingEngineAdapter,
)


def create_embed_batch_use_case(
    *,
    session: AsyncSession,
    max_attempts: int = 3,
) -> EmbedBatchUseCase:

    return EmbedBatchUseCase(
        task_repository=EmbeddingTaskRepositoryImpl(
            session=session,
        ),
        chunk_reader=ModuleChunkReader(
            session=session,
        ),
        embedding_engine=LegacyEmbeddingEngineAdapter(),
        embedding_repository=(
            DocumentChunkEmbeddingRepositoryImpl(
                session=session,
            )
        ),
        batch_finalizer=ModuleBatchFinalizer(
            session=session,
        ),
        uow=SQLAlchemyUnitOfWork(
            session=session,
        ),
        max_attempts=max_attempts,
    )


@asynccontextmanager
async def create_embed_batch_use_case_scope(
    *,
    session_factory,
    max_attempts: int = 3,
) -> AsyncIterator[EmbedBatchUseCase]:

    async with session_factory() as session:
        yield create_embed_batch_use_case(
            session=session,
            max_attempts=max_attempts,
        )
