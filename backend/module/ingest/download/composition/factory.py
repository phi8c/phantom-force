from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.ingest.download.application.use_cases.download_file import (
    DownloadFileUseCase,
)
from module.ingest.download.domain.contracts.document_source import (
    DocumentSource,
)
from module.ingest.download.domain.contracts.object_storage import (
    ObjectStorage,
)
from module.ingest.download.infrastructure.persistence.repositories.download_task_repository_impl import (
    DownloadTaskRepositoryImpl,
)
from module.ingest.download.infrastructure.persistence.repositories.storage_asset_repository_impl import (
    StorageAssetRepositoryImpl,
)
from module.ingest.download.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from module.ingest.download.domain.contracts.extraction_task_scheduler import (
    ExtractionTaskScheduler,
)
from module.ingest.orchestration.composition import (
    create_orchestration_progress_service,
)


def create_download_file_use_case(
    *,
    session,
    document_source: DocumentSource,
    object_storage: ObjectStorage,
    extraction_task_scheduler: ExtractionTaskScheduler,
    max_attempts: int = 3,
) -> DownloadFileUseCase:

    task_repository = DownloadTaskRepositoryImpl(
        session=session,
    )

    storage_asset_repository = (
        StorageAssetRepositoryImpl(
            session=session,
        )
    )

    uow = SQLAlchemyUnitOfWork(
        session=session,
    )

    return DownloadFileUseCase(
        task_repository=task_repository,
        document_source=document_source,
        object_storage=object_storage,
        storage_asset_repository=(
            storage_asset_repository
        ),
        extraction_task_scheduler=extraction_task_scheduler,
        orchestration_progress_service=(
            create_orchestration_progress_service(
                session=session,
            )
        ),
        uow=uow,
        max_attempts=max_attempts,
    )


@asynccontextmanager
async def create_download_file_use_case_scope(
    *,
    session_factory,
    document_source: DocumentSource,
    object_storage: ObjectStorage,
    extraction_task_scheduler: ExtractionTaskScheduler,
    max_attempts: int = 3,
) -> AsyncIterator[DownloadFileUseCase]:

    async with session_factory() as session:
        yield create_download_file_use_case(
            session=session,
            document_source=document_source,
            object_storage=object_storage,
            extraction_task_scheduler=(
                extraction_task_scheduler
            ),
            max_attempts=max_attempts,
        )
