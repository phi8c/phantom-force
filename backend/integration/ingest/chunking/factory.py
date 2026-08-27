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

from integration.ingest.chunking.chunking_engine import (
    LegacyChunkingEngineAdapter,
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
