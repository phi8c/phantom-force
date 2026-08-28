from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.extraction.application.use_cases.extract_document import (
    ExtractDocumentUseCase,
)
from module.ingest.extraction.domain.contracts.chunking_task_scheduler import (
    ChunkingTaskScheduler,
)
from module.ingest.chunking.domain.contracts.chunking_dispatcher import (
    ChunkingDispatcher,
)
from module.ingest.chunking.infrastructure.persistence.repositories.chunking_task_repository_impl import (
    ChunkingTaskRepositoryImpl,
)
from module.ingest.extraction.domain.contracts.object_storage import (
    ObjectStorage,
)
from module.ingest.extraction.infrastructure.persistence.repositories.extraction_task_repository_impl import (
    ExtractionTaskRepositoryImpl,
)
from module.ingest.extraction.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)

from integration.ingest.extraction.extraction_engine_resolver import (
    DbExtractionEngineResolver,
)
from integration.ingest.extraction.source_asset_reader import (
    StorageSourceAssetReader,
)
from integration.ingest.extraction.storage_asset_repository import (
    ModuleStorageAssetRepository,
)


def create_extract_document_use_case(
    *,
    session: AsyncSession,
    file_storage,
    object_storage: ObjectStorage,
    chunking_task_scheduler: ChunkingTaskScheduler,
    max_attempts: int = 3,
) -> ExtractDocumentUseCase:

    task_repository = ExtractionTaskRepositoryImpl(
        session=session,
    )

    storage_asset_repository = (
        ModuleStorageAssetRepository(
            session=session,
        )
    )

    source_asset_reader = StorageSourceAssetReader(
        session=session,
        file_storage=file_storage,
    )

    uow = SQLAlchemyUnitOfWork(
        session=session,
    )

    return ExtractDocumentUseCase(
        task_repository=task_repository,
        source_asset_reader=source_asset_reader,
        extraction_engine_resolver=(
            DbExtractionEngineResolver(
                session=session,
            )
        ),
        object_storage=object_storage,
        storage_asset_repository=(
            storage_asset_repository
        ),
        chunking_task_scheduler=(
            chunking_task_scheduler
        ),
        uow=uow,
        max_attempts=max_attempts,
    )


def create_extract_document_use_case_with_chunking(
    *,
    session: AsyncSession,
    file_storage,
    object_storage: ObjectStorage,
    chunking_dispatcher: ChunkingDispatcher,
    max_attempts: int = 3,
) -> ExtractDocumentUseCase:
    from integration.ingest.extraction.chunking_task_scheduler import (
        ModuleChunkingTaskScheduler,
    )

    return create_extract_document_use_case(
        session=session,
        file_storage=file_storage,
        object_storage=object_storage,
        chunking_task_scheduler=(
            ModuleChunkingTaskScheduler(
                task_repository=(
                    ChunkingTaskRepositoryImpl(
                        session=session,
                    )
                ),
                dispatcher=chunking_dispatcher,
            )
        ),
        max_attempts=max_attempts,
    )


@asynccontextmanager
async def create_extract_document_use_case_scope_with_chunking(
    *,
    session_factory,
    file_storage,
    object_storage: ObjectStorage,
    chunking_dispatcher: ChunkingDispatcher,
    max_attempts: int = 3,
) -> AsyncIterator[ExtractDocumentUseCase]:

    async with session_factory() as session:
        yield create_extract_document_use_case_with_chunking(
            session=session,
            file_storage=file_storage,
            object_storage=object_storage,
            chunking_dispatcher=(
                chunking_dispatcher
            ),
            max_attempts=max_attempts,
        )
