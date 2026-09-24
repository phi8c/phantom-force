from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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
from module.ingest.orchestration.composition import (
    create_orchestration_progress_service,
)

from workers.ingest.chunking_worker import ChunkingWorker
from workers.ingest.classification_worker import (
    ClassificationWorker,
)
from workers.ingest.download_worker import DownloadWorker
from workers.ingest.discovery_worker import DiscoveryWorker
from workers.ingest.embedding_worker import EmbeddingWorker
from workers.ingest.extraction_worker import ExtractionWorker

from bootstrap.database import async_session_factory
from bootstrap.modules import chunking_use_case_scope
from bootstrap.modules import classification_use_case_scope
from bootstrap.modules import discovery_use_case_scope
from bootstrap.modules import download_use_case_scope
from bootstrap.modules import embedding_use_case_scope
from bootstrap.modules import extraction_use_case_scope
from bootstrap.queues import IngestConsumers
from bootstrap.queues import IngestDispatchers


@asynccontextmanager
async def _download_claim_scope() -> AsyncIterator[tuple]:
    async with async_session_factory() as session:
        try:
            yield (
                DownloadTaskRepositoryImpl(
                    session=session,
                ),
                DownloadUnitOfWork(
                    session=session,
                ),
                create_orchestration_progress_service(
                    session=session,
                ),
            )
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def _extraction_claim_scope() -> AsyncIterator[tuple]:
    async with async_session_factory() as session:
        try:
            yield (
                ExtractionTaskRepositoryImpl(
                    session=session,
                ),
                ExtractionUnitOfWork(
                    session=session,
                ),
                create_orchestration_progress_service(
                    session=session,
                ),
            )
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def _chunking_claim_scope() -> AsyncIterator[tuple]:
    async with async_session_factory() as session:
        try:
            yield (
                ChunkingTaskRepositoryImpl(
                    session=session,
                ),
                ChunkingUnitOfWork(
                    session=session,
                ),
                create_orchestration_progress_service(
                    session=session,
                ),
            )
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def _embedding_claim_scope() -> AsyncIterator[tuple]:
    async with async_session_factory() as session:
        try:
            yield (
                EmbeddingTaskRepositoryImpl(
                    session=session,
                ),
                EmbeddingUnitOfWork(
                    session=session,
                ),
                create_orchestration_progress_service(
                    session=session,
                ),
            )
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def _classification_claim_scope() -> AsyncIterator[tuple]:
    async with async_session_factory() as session:
        try:
            yield (
                ClassificationTaskRepositoryImpl(
                    session=session,
                ),
                ClassificationUnitOfWork(
                    session=session,
                ),
                create_orchestration_progress_service(
                    session=session,
                ),
            )
        except Exception:
            await session.rollback()
            raise


def create_discovery_worker(
    *,
    consumers: IngestConsumers,
    dispatchers: IngestDispatchers,
    data_hub_provider_resolver,
) -> DiscoveryWorker:

    return DiscoveryWorker(
        consumer=consumers.discovery,
        use_case_factory=lambda: discovery_use_case_scope(
            data_hub_provider_resolver=(
                data_hub_provider_resolver
            ),
            download_dispatcher=dispatchers.download,
        ),
        discovery_dispatcher=dispatchers.discovery,
    )


def create_download_worker(
    *,
    consumers: IngestConsumers,
    dispatchers: IngestDispatchers,
    document_source,
    object_storage,
) -> DownloadWorker:

    return DownloadWorker(
        consumer=consumers.download,
        claim_scope_factory=_download_claim_scope,
        use_case_factory=lambda: download_use_case_scope(
            document_source=document_source,
            object_storage=object_storage,
            extraction_dispatcher=(
                dispatchers.extraction
            ),
        ),
        extraction_dispatcher=(
            dispatchers.extraction
        ),
    )


def create_extraction_worker(
    *,
    consumers: IngestConsumers,
    dispatchers: IngestDispatchers,
    file_storage,
    object_storage,
) -> ExtractionWorker:

    return ExtractionWorker(
        consumer=consumers.extraction,
        claim_scope_factory=_extraction_claim_scope,
        use_case_factory=lambda: extraction_use_case_scope(
            file_storage=file_storage,
            object_storage=object_storage,
            chunking_dispatcher=dispatchers.chunking,
        ),
    )


def create_chunking_worker(
    *,
    consumers: IngestConsumers,
    dispatchers: IngestDispatchers,
    file_storage,
) -> ChunkingWorker:

    return ChunkingWorker(
        consumer=consumers.chunking,
        claim_scope_factory=_chunking_claim_scope,
        use_case_factory=lambda: chunking_use_case_scope(
            file_storage=file_storage,
            embedding_dispatcher=(
                dispatchers.embedding
            ),
            classification_dispatcher=(
                dispatchers.classification
            ),
        ),
    )


def create_embedding_worker(
    *,
    consumers: IngestConsumers,
) -> EmbeddingWorker:

    return EmbeddingWorker(
        consumer=consumers.embedding,
        claim_scope_factory=_embedding_claim_scope,
        use_case_factory=embedding_use_case_scope,
    )


def create_classification_worker(
    *,
    consumers: IngestConsumers,
    file_storage,
) -> ClassificationWorker:

    return ClassificationWorker(
        consumer=consumers.classification,
        claim_scope_factory=_classification_claim_scope,
        use_case_factory=lambda: classification_use_case_scope(
            file_storage=file_storage,
        ),
    )
