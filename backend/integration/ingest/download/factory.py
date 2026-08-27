from sqlalchemy.ext.asyncio import AsyncSession

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
from module.ingest.extraction.domain.contracts.extraction_dispatcher import (
    ExtractionDispatcher,
)
from module.ingest.extraction.infrastructure.persistence.repositories.extraction_task_repository_impl import (
    ExtractionTaskRepositoryImpl,
)

from integration.ingest.download.extraction_task_scheduler import (
    ModuleExtractionTaskScheduler,
)


def create_download_file_use_case(
    *,
    session: AsyncSession,
    document_source: DocumentSource,
    object_storage: ObjectStorage,
    extraction_dispatcher: ExtractionDispatcher,
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

    extraction_task_repository = (
        ExtractionTaskRepositoryImpl(
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
        extraction_task_scheduler=(
            ModuleExtractionTaskScheduler(
                task_repository=(
                    extraction_task_repository
                ),
                dispatcher=(
                    extraction_dispatcher
                ),
            )
        ),
        uow=uow,
        max_attempts=max_attempts,
    )
