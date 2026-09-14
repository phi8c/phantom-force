from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.ingest.extraction.application.use_cases.extract_document import (
    ExtractDocumentUseCase,
)
from module.ingest.extraction.domain.contracts.chunking_task_scheduler import (
    ChunkingTaskScheduler,
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
from module.ingest.extraction.infrastructure.engine.extraction_engine_resolver import (
    DbExtractionEngineResolver,
)
from module.ingest.extraction.domain.contracts.source_asset_reader import (
    SourceAssetReader,
)
from module.ingest.extraction.infrastructure.persistence.repositories.storage_asset_repository import (
    ModuleStorageAssetRepository,
)
from module.ingest.orchestration.composition import (
    create_orchestration_progress_service,
)


def create_extract_document_use_case(
    *,
    session,
    source_asset_reader: SourceAssetReader,
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
        orchestration_progress_service=(
            create_orchestration_progress_service(
                session=session,
            )
        ),
        uow=uow,
        max_attempts=max_attempts,
    )


@asynccontextmanager
async def create_extract_document_use_case_scope(
    *,
    session_factory,
    source_asset_reader: SourceAssetReader,
    object_storage: ObjectStorage,
    chunking_task_scheduler: ChunkingTaskScheduler,
    max_attempts: int = 3,
) -> AsyncIterator[ExtractDocumentUseCase]:

    async with session_factory() as session:
        yield create_extract_document_use_case(
            session=session,
            source_asset_reader=source_asset_reader,
            object_storage=object_storage,
            chunking_task_scheduler=(
                chunking_task_scheduler
            ),
            max_attempts=max_attempts,
        )
