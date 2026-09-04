from contextlib import asynccontextmanager

from integration.ingest.chunking.factory import (
    create_chunk_document_use_case_scope_with_downstream,
)
from integration.ingest.classification.factory import (
    create_classify_batch_use_case_scope,
)
from integration.ingest.discovery.factory import (
    create_discover_batch_use_case_scope,
)
from integration.ingest.download.factory import (
    create_download_file_use_case_scope,
)
from integration.ingest.embedding.factory import (
    create_embed_batch_use_case_scope,
)
from integration.ingest.extraction.factory import (
    create_extract_document_use_case_scope_with_chunking,
)

from bootstrap.database import async_session_factory
from module.ingest.config.application.use_cases.start_ingestion import (
    StartIngestionUseCase,
)
from module.ingest.config.infrastructure.persistence.repositories.ingestion_config_repository_impl import (
    IngestionConfigRepositoryImpl,
)
from module.ingest.config.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork as IngestionConfigUnitOfWork,
)
from module.ingest.master.chunking_strategy.infrastructure.persistence.repositories.chunking_strategy_repository_impl import (
    ChunkingStrategyRepositoryImpl,
)
from module.ingest.master.extraction_strategy.infrastructure.persistence.repositories.extraction_strategy_repository_impl import (
    ExtractionStrategyRepositoryImpl,
)
from module.ingest.master.model_set.infrastructure.persistence.repositories.model_set_repository_impl import (
    ModelSetRepositoryImpl,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_repository_impl import (
    KnowledgeSpaceRepositoryImpl,
)


@asynccontextmanager
async def start_ingestion_use_case_scope(
    *,
    discovery_dispatcher,
):

    async with async_session_factory() as session:
        yield StartIngestionUseCase(
            knowledge_space_repository=(
                KnowledgeSpaceRepositoryImpl(
                    session,
                )
            ),
            ingestion_config_repository=(
                IngestionConfigRepositoryImpl(
                    session,
                )
            ),
            extraction_strategy_repository=(
                ExtractionStrategyRepositoryImpl(
                    session,
                )
            ),
            chunking_strategy_repository=(
                ChunkingStrategyRepositoryImpl(
                    session,
                )
            ),
            model_set_repository=(
                ModelSetRepositoryImpl(
                    session,
                )
            ),
            discovery_dispatcher=discovery_dispatcher,
            uow=IngestionConfigUnitOfWork(
                session,
            ),
        )


def download_use_case_scope(
    *,
    document_source,
    object_storage,
    extraction_dispatcher,
):

    return create_download_file_use_case_scope(
        session_factory=async_session_factory,
        document_source=document_source,
        object_storage=object_storage,
        extraction_dispatcher=extraction_dispatcher,
    )


def discovery_use_case_scope(
    *,
    data_hub_provider_resolver,
    download_dispatcher,
):

    return create_discover_batch_use_case_scope(
        session_factory=async_session_factory,
        data_hub_provider_resolver=(
            data_hub_provider_resolver
        ),
        download_dispatcher=download_dispatcher,
    )


def extraction_use_case_scope(
    *,
    file_storage,
    object_storage,
    chunking_dispatcher,
):

    return (
        create_extract_document_use_case_scope_with_chunking(
            session_factory=async_session_factory,
            file_storage=file_storage,
            object_storage=object_storage,
            chunking_dispatcher=chunking_dispatcher,
        )
    )


def chunking_use_case_scope(
    *,
    file_storage,
    embedding_dispatcher,
    classification_dispatcher,
):

    return (
        create_chunk_document_use_case_scope_with_downstream(
            session_factory=async_session_factory,
            file_storage=file_storage,
            embedding_dispatcher=embedding_dispatcher,
            classification_dispatcher=(
                classification_dispatcher
            ),
        )
    )


def embedding_use_case_scope():

    return create_embed_batch_use_case_scope(
        session_factory=async_session_factory,
    )


def classification_use_case_scope():

    return create_classify_batch_use_case_scope(
        session_factory=async_session_factory,
    )
