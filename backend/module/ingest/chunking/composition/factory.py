from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.ingest.chunking.application.use_cases.chunk_document import (
    ChunkDocumentUseCase,
)
from module.ingest.chunking.domain.contracts.downstream_task_scheduler import (
    DownstreamTaskScheduler,
)
from module.ingest.chunking.domain.contracts.extracted_asset_reader import (
    ExtractedAssetReader,
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
from module.ingest.chunking.infrastructure.engine.chunking_engine_resolver import (
    DbChunkingEngineResolver,
)
from module.ingest.orchestration.composition import (
    create_orchestration_progress_service,
)


def create_chunk_document_use_case(
    *,
    session,
    extracted_asset_reader: ExtractedAssetReader,
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
        extracted_asset_reader=extracted_asset_reader,
        chunking_engine_resolver=(
            DbChunkingEngineResolver(
                session=session,
            )
        ),
        chunk_batch_writer=ChunkBatchWriterImpl(
            session=session,
        ),
        downstream_task_scheduler=(
            downstream_task_scheduler
        ),
        orchestration_progress_service=(
            create_orchestration_progress_service(
                session=session,
            )
        ),
        uow=uow,
        max_attempts=max_attempts,
    )


@asynccontextmanager
async def create_chunk_document_use_case_scope(
    *,
    session_factory,
    extracted_asset_reader: ExtractedAssetReader,
    downstream_task_scheduler: DownstreamTaskScheduler,
    max_attempts: int = 3,
) -> AsyncIterator[ChunkDocumentUseCase]:

    async with session_factory() as session:
        yield create_chunk_document_use_case(
            session=session,
            extracted_asset_reader=extracted_asset_reader,
            downstream_task_scheduler=(
                downstream_task_scheduler
            ),
            max_attempts=max_attempts,
        )
