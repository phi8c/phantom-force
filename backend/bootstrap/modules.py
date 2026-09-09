from contextlib import asynccontextmanager

from module.ingest.chunking.composition.factory import (
    create_chunk_document_use_case,
)
from module.ingest.classification.composition.factory import (
    create_classify_batch_use_case,
)
from module.ingest.discovery.composition.factory import (
    create_discover_batch_use_case,
)
from module.ingest.download.composition.factory import (
    create_download_file_use_case,
)
from module.ingest.embedding.composition.factory import (
    create_embed_batch_use_case,
)
from module.ingest.extraction.composition.factory import (
    create_extract_document_use_case,
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
from module.ingest.download.infrastructure.persistence.repositories.download_task_repository_impl import (
    DownloadTaskRepositoryImpl,
)
from module.ingest.download.composition import (
    DownloadTaskSchedulingService,
)
from module.ingest.extraction.infrastructure.persistence.repositories.extraction_task_repository_impl import (
    ExtractionTaskRepositoryImpl,
)
from module.ingest.extraction.composition import (
    ExtractionTaskSchedulingService,
)
from module.ingest.chunking.infrastructure.persistence.repositories.chunking_task_repository_impl import (
    ChunkingTaskRepositoryImpl,
)
from module.ingest.chunking.composition import (
    ChunkingTaskSchedulingService,
)
from module.ingest.embedding.infrastructure.persistence.repositories.embedding_task_repository_impl import (
    EmbeddingTaskRepositoryImpl,
)
from module.ingest.embedding.composition import (
    EmbeddingTaskSchedulingService,
)
from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import (
    ClassificationTaskRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.repositories.chunk_classification_repository_impl import (
    ChunkClassificationRepositoryImpl,
)
from module.ingest.classification.composition import (
    ClassificationTaskSchedulingService,
)
from module.ingest.download.infrastructure.persistence.queries.source_asset_query import (
    SourceAssetQuery,
)
from module.ingest.extraction.infrastructure.persistence.queries.extracted_asset_query import (
    ExtractedAssetQuery,
)
from module.ingest.chunking.infrastructure.persistence.queries.chunk_batch_completion_service import (
    ChunkBatchCompletionService,
)
from module.ingest.chunking.infrastructure.persistence.queries.document_chunk_query import (
    DocumentChunkQuery,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_repository_impl import (
    KnowledgeSpaceRepositoryImpl,
)
from integration.ingest.discovery.download_task_scheduler import (
    ModuleDownloadTaskScheduler,
)
from integration.ingest.download.extraction_task_scheduler import (
    ModuleExtractionTaskScheduler,
)
from integration.ingest.extraction.chunking_task_scheduler import (
    ModuleChunkingTaskScheduler,
)
from integration.ingest.extraction.source_asset_reader import (
    StorageSourceAssetReader,
)
from integration.ingest.chunking.downstream_task_scheduler import (
    ModuleDownstreamTaskScheduler,
)
from integration.ingest.chunking.extracted_asset_reader import (
    StorageExtractedAssetReader,
)
from integration.ingest.embedding.batch_finalizer import (
    ModuleBatchFinalizer as EmbeddingBatchFinalizer,
)
from integration.ingest.embedding.chunk_reader import (
    ModuleChunkReader as EmbeddingChunkReader,
)
from integration.ingest.classification.batch_finalizer import (
    ModuleBatchFinalizer as ClassificationBatchFinalizer,
)
from integration.ingest.classification.chunk_reader import (
    ModuleChunkReader as ClassificationChunkReader,
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

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            yield create_download_file_use_case(
                session=session,
                document_source=document_source,
                object_storage=object_storage,
                extraction_task_scheduler=(
                    ModuleExtractionTaskScheduler(
                        scheduling_service=(
                            ExtractionTaskSchedulingService(
                                task_repository=(
                                    ExtractionTaskRepositoryImpl(
                                        session=session,
                                    )
                                ),
                            )
                        ),
                        dispatcher=extraction_dispatcher,
                    )
                ),
            )

    return scope()


def discovery_use_case_scope(
    *,
    data_hub_provider_resolver,
    download_dispatcher,
):

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            yield create_discover_batch_use_case(
                session=session,
                data_hub_provider_resolver=(
                    data_hub_provider_resolver
                ),
                download_task_scheduler=(
                    ModuleDownloadTaskScheduler(
                        scheduling_service=(
                            DownloadTaskSchedulingService(
                                task_repository=(
                                    DownloadTaskRepositoryImpl(
                                        session=session,
                                    )
                                ),
                            )
                        ),
                        dispatcher=download_dispatcher,
                    )
                ),
            )

    return scope()


def extraction_use_case_scope(
    *,
    file_storage,
    object_storage,
    chunking_dispatcher,
):

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            yield create_extract_document_use_case(
                session=session,
                source_asset_reader=(
                    StorageSourceAssetReader(
                        source_asset_query=SourceAssetQuery(
                            session=session,
                        ),
                        file_storage=file_storage,
                    )
                ),
                object_storage=object_storage,
                chunking_task_scheduler=(
                    ModuleChunkingTaskScheduler(
                        scheduling_service=(
                            ChunkingTaskSchedulingService(
                                task_repository=(
                                    ChunkingTaskRepositoryImpl(
                                        session=session,
                                    )
                                ),
                            )
                        ),
                        dispatcher=chunking_dispatcher,
                    )
                ),
            )

    return scope()


def chunking_use_case_scope(
    *,
    file_storage,
    embedding_dispatcher,
    classification_dispatcher,
):

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            yield create_chunk_document_use_case(
                session=session,
                extracted_asset_reader=(
                    StorageExtractedAssetReader(
                        extracted_asset_query=(
                            ExtractedAssetQuery(
                                session=session,
                            )
                        ),
                        file_storage=file_storage,
                    )
                ),
                downstream_task_scheduler=(
                    ModuleDownstreamTaskScheduler(
                        batch_completion_service=(
                            ChunkBatchCompletionService(
                                session=session,
                            )
                        ),
                        embedding_scheduling_service=(
                            EmbeddingTaskSchedulingService(
                                task_repository=(
                                    EmbeddingTaskRepositoryImpl(
                                        session=session,
                                    )
                                ),
                            )
                        ),
                        classification_scheduling_service=(
                            ClassificationTaskSchedulingService(
                                ingestion_config_repository=(
                                    IngestionConfigRepositoryImpl(
                                        session=session,
                                    )
                                ),
                                task_repository=(
                                    ClassificationTaskRepositoryImpl(
                                        session=session,
                                    )
                                ),
                                classification_repository=(
                                    ChunkClassificationRepositoryImpl(
                                        session=session,
                                    )
                                ),
                                chunk_query=DocumentChunkQuery(
                                    session=session,
                                ),
                            )
                        ),
                        embedding_dispatcher=(
                            embedding_dispatcher
                        ),
                        classification_dispatcher=(
                            classification_dispatcher
                        ),
                    )
                ),
            )

    return scope()


def embedding_use_case_scope():

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            completion_service = ChunkBatchCompletionService(
                session=session,
            )

            yield create_embed_batch_use_case(
                session=session,
                chunk_reader=EmbeddingChunkReader(
                    chunk_query=DocumentChunkQuery(
                        session=session,
                    ),
                ),
                batch_finalizer=EmbeddingBatchFinalizer(
                    completion_service=completion_service,
                ),
            )

    return scope()


def classification_use_case_scope(
    *,
    file_storage,
):

    @asynccontextmanager
    async def scope():
        async with async_session_factory() as session:
            completion_service = ChunkBatchCompletionService(
                session=session,
            )

            yield create_classify_batch_use_case(
                session=session,
                chunk_reader=ClassificationChunkReader(
                    chunk_query=DocumentChunkQuery(
                        session=session,
                    ),
                ),
                extracted_asset_reader=(
                    StorageExtractedAssetReader(
                        extracted_asset_query=(
                            ExtractedAssetQuery(
                                session=session,
                            )
                        ),
                        file_storage=file_storage,
                    )
                ),
                batch_finalizer=ClassificationBatchFinalizer(
                    completion_service=completion_service,
                ),
            )

    return scope()
