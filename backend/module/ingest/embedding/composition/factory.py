from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.ingest.embedding.application.use_cases.embed_batch import (
    EmbedBatchUseCase,
)
from module.ingest.embedding.domain.contracts.batch_finalizer import (
    BatchFinalizer,
)
from module.ingest.embedding.domain.contracts.chunk_reader import (
    ChunkReader,
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

from module.ingest.embedding.infrastructure.engine.embedding_engine_resolver import (
    DbEmbeddingEngineResolver,
)


def create_embed_batch_use_case(
    *,
    session,
    chunk_reader: ChunkReader,
    batch_finalizer: BatchFinalizer,
    max_attempts: int = 3,
) -> EmbedBatchUseCase:

    return EmbedBatchUseCase(
        task_repository=EmbeddingTaskRepositoryImpl(
            session=session,
        ),
        chunk_reader=chunk_reader,
        embedding_engine_resolver=(
            DbEmbeddingEngineResolver(
                session=session,
            )
        ),
        embedding_repository=(
            DocumentChunkEmbeddingRepositoryImpl(
                session=session,
            )
        ),
        batch_finalizer=batch_finalizer,
        uow=SQLAlchemyUnitOfWork(
            session=session,
        ),
        max_attempts=max_attempts,
    )


async def create_text_embedding_provider(
    *,
    session,
    knowledge_space_id,
):

    return await DbEmbeddingEngineResolver(
        session=session,
    ).resolve_for_knowledge_space(
        knowledge_space_id,
    )


@asynccontextmanager
async def create_embed_batch_use_case_scope(
    *,
    session_factory,
    chunk_reader: ChunkReader,
    batch_finalizer: BatchFinalizer,
    max_attempts: int = 3,
) -> AsyncIterator[EmbedBatchUseCase]:

    async with session_factory() as session:
        yield create_embed_batch_use_case(
            session=session,
            chunk_reader=chunk_reader,
            batch_finalizer=batch_finalizer,
            max_attempts=max_attempts,
        )
