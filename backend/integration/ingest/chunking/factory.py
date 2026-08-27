from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.chunking.application.use_cases.chunk_document import (
    ChunkDocumentUseCase,
)
from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamTaskScheduler,
)
from module.ingest.chunking.infrastructure.persistence.repositories.chunk_batch_writer_impl import (
    ChunkBatchWriterImpl,
)
from module.ingest.chunking.infrastructure.persistence.repositories.chunking_task_repository_impl import (
    ChunkingTaskRepositoryImpl,
)
from module.ingest.chunking.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from module.ingest.classification.domain.contracts.classification_dispatcher import (
    ClassificationDispatcher,
)
from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import (
    ClassificationTaskRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.repositories.chunk_classification_repository_impl import (
    ChunkClassificationRepositoryImpl,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.embedding.domain.contracts.embedding_dispatcher import (
    EmbeddingDispatcher,
)
from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import (
    EmbeddingTaskRepositoryImpl,
)

from integration.ingest.chunking.chunking_engine import (
    LegacyChunkingEngineAdapter,
)
from integration.ingest.chunking.downstream_task_scheduler import (
    ModuleDownstreamTaskScheduler,
)
from integration.ingest.chunking.extracted_asset_reader import (
    StorageExtractedAssetReader,
)


def create_chunk_document_use_case(
    *,
    session: AsyncSession,
    file_storage,
    downstream_task_scheduler: DownstreamTaskScheduler,
    max_attempts: int = 3,
) -> ChunkDocumentUseCase:

    task_repository = ChunkingTaskRepositoryImpl(
        session=session,
    )

    uow = SQLAlchemyUnitOfWork(
        session=session,
    )

    return ChunkDocumentUseCase(
        task_repository=task_repository,
        extracted_asset_reader=(
            StorageExtractedAssetReader(
                session=session,
                file_storage=file_storage,
            )
        ),
        chunking_engine=(
            LegacyChunkingEngineAdapter()
        ),
        chunk_batch_writer=ChunkBatchWriterImpl(
            session=session,
        ),
        downstream_task_scheduler=(
            downstream_task_scheduler
        ),
        uow=uow,
        max_attempts=max_attempts,
    )


def create_downstream_task_scheduler(
    *,
    session: AsyncSession,
    embedding_dispatcher: EmbeddingDispatcher,
    classification_dispatcher: ClassificationDispatcher,
) -> DownstreamTaskScheduler:

    return ModuleDownstreamTaskScheduler(
        session=session,
        ingestion_config_repository=(
            IngestionConfigRepositoryImpl(
                session=session,
            )
        ),
        embedding_task_repository=(
            EmbeddingTaskRepositoryImpl(
                session=session,
            )
        ),
        classification_task_repository=(
            ClassificationTaskRepositoryImpl(
                session=session,
            )
        ),
        chunk_classification_repository=(
            ChunkClassificationRepositoryImpl(
                session=session,
            )
        ),
        embedding_dispatcher=embedding_dispatcher,
        classification_dispatcher=(
            classification_dispatcher
        ),
    )


@asynccontextmanager
async def create_chunk_document_use_case_scope(
    *,
    session_factory,
    file_storage,
    downstream_task_scheduler: DownstreamTaskScheduler,
    max_attempts: int = 3,
) -> AsyncIterator[ChunkDocumentUseCase]:

    async with session_factory() as session:
        yield create_chunk_document_use_case(
            session=session,
            file_storage=file_storage,
            downstream_task_scheduler=(
                downstream_task_scheduler
            ),
            max_attempts=max_attempts,
        )


@asynccontextmanager
async def create_chunk_document_use_case_scope_with_downstream(
    *,
    session_factory,
    file_storage,
    embedding_dispatcher: EmbeddingDispatcher,
    classification_dispatcher: ClassificationDispatcher,
    max_attempts: int = 3,
) -> AsyncIterator[ChunkDocumentUseCase]:

    async with session_factory() as session:
        yield create_chunk_document_use_case(
            session=session,
            file_storage=file_storage,
            downstream_task_scheduler=(
                create_downstream_task_scheduler(
                    session=session,
                    embedding_dispatcher=(
                        embedding_dispatcher
                    ),
                    classification_dispatcher=(
                        classification_dispatcher
                    ),
                )
            ),
            max_attempts=max_attempts,
        )
