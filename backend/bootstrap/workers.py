from module.ingest.chunking.infrastructure.persistence.repositories.chunking_task_repository_impl import (
    ChunkingTaskRepositoryImpl,
)
from module.ingest.chunking.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as ChunkingUnitOfWork,
)
from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import (
    ClassificationTaskRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as ClassificationUnitOfWork,
)
from module.ingest.download.infrastructure.persistence.repositories.download_task_repository_impl import (
    DownloadTaskRepositoryImpl,
)
from module.ingest.download.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as DownloadUnitOfWork,
)
from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import (
    EmbeddingTaskRepositoryImpl,
)
from module.ingest.embedding.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as EmbeddingUnitOfWork,
)
from module.ingest.extraction.infrastructure.persistence.repositories.extraction_task_repository_impl import (
    ExtractionTaskRepositoryImpl,
)
from module.ingest.extraction.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as ExtractionUnitOfWork,
)

from workers.ingest.chunking_worker import ChunkingWorker
from workers.ingest.classification_worker import (
    ClassificationWorker,
)
from workers.ingest.download_worker import DownloadWorker
from workers.ingest.embedding_worker import EmbeddingWorker
from workers.ingest.extraction_worker import ExtractionWorker

from bootstrap.database import async_session_factory
from bootstrap.modules import chunking_use_case_scope
from bootstrap.modules import classification_use_case_scope
from bootstrap.modules import download_use_case_scope
from bootstrap.modules import embedding_use_case_scope
from bootstrap.modules import extraction_use_case_scope
from bootstrap.queues import IngestQueueClients
from bootstrap.queues import IngestDispatchers


def _claim_session():
    return async_session_factory()


def create_download_worker(
    *,
    queues: IngestQueueClients,
    dispatchers: IngestDispatchers,
    document_source,
    object_storage,
) -> DownloadWorker:

    session = _claim_session()

    return DownloadWorker(
        queue_client=queues.download,
        task_repository=DownloadTaskRepositoryImpl(
            session=session,
        ),
        use_case_factory=lambda: download_use_case_scope(
            document_source=document_source,
            object_storage=object_storage,
            extraction_dispatcher=(
                dispatchers.extraction
            ),
        ),
        uow=DownloadUnitOfWork(
            session=session,
        ),
    )


def create_extraction_worker(
    *,
    queues: IngestQueueClients,
    dispatchers: IngestDispatchers,
    file_storage,
    object_storage,
) -> ExtractionWorker:

    session = _claim_session()

    return ExtractionWorker(
        queue_client=queues.extraction,
        task_repository=ExtractionTaskRepositoryImpl(
            session=session,
        ),
        use_case_factory=lambda: extraction_use_case_scope(
            file_storage=file_storage,
            object_storage=object_storage,
            chunking_dispatcher=dispatchers.chunking,
        ),
        uow=ExtractionUnitOfWork(
            session=session,
        ),
    )


def create_chunking_worker(
    *,
    queues: IngestQueueClients,
    dispatchers: IngestDispatchers,
    file_storage,
) -> ChunkingWorker:

    session = _claim_session()

    return ChunkingWorker(
        queue_client=queues.chunking,
        task_repository=ChunkingTaskRepositoryImpl(
            session=session,
        ),
        use_case_factory=lambda: chunking_use_case_scope(
            file_storage=file_storage,
            embedding_dispatcher=(
                dispatchers.embedding
            ),
            classification_dispatcher=(
                dispatchers.classification
            ),
        ),
        uow=ChunkingUnitOfWork(
            session=session,
        ),
    )


def create_embedding_worker(
    *,
    queues: IngestQueueClients,
) -> EmbeddingWorker:

    session = _claim_session()

    return EmbeddingWorker(
        queue_client=queues.embedding,
        task_repository=EmbeddingTaskRepositoryImpl(
            session=session,
        ),
        use_case_factory=embedding_use_case_scope,
        uow=EmbeddingUnitOfWork(
            session=session,
        ),
    )


def create_classification_worker(
    *,
    queues: IngestQueueClients,
) -> ClassificationWorker:

    session = _claim_session()

    return ClassificationWorker(
        queue_client=queues.classification,
        task_repository=ClassificationTaskRepositoryImpl(
            session=session,
        ),
        use_case_factory=classification_use_case_scope,
        uow=ClassificationUnitOfWork(
            session=session,
        ),
    )
