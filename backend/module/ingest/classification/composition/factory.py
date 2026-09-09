from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from module.ai.llm.composition import (
    create_llm_gateway,
)
from module.ingest.config.composition import (
    create_ingestion_config_service,
)
from module.ingest.classification.application.use_cases.classify_batch import (
    ClassifyBatchUseCase,
)
from module.ingest.classification.domain.contracts.batch_finalizer import (
    BatchFinalizer,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkReader,
)
from module.ingest.chunking.composition import (
    ExtractedAssetReader,
)
from module.ingest.classification.infrastructure.persistence.repositories.chunk_classification_repository_impl import (
    ChunkClassificationRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.repositories.classification_task_repository_impl import (
    ClassificationTaskRepositoryImpl,
)
from module.ingest.classification.infrastructure.persistence.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from module.ingest.classification.infrastructure.engine.llm_classification_engine import (
    LLMClassificationEngine,
)
from module.ingest.classification.infrastructure.engine.llm_document_structure_analyzer import (
    LLMDocumentStructureAnalyzer,
)
from module.ingest.knowledge.composition import (
    create_knowledge_writer,
)
from module.prompt.composition import (
    create_prompt_provider,
)


def create_classify_batch_use_case(
    *,
    session,
    chunk_reader: ChunkReader,
    batch_finalizer: BatchFinalizer,
    document_structure_analyzer=None,
    extracted_asset_reader: ExtractedAssetReader | None = None,
    max_attempts: int = 3,
) -> ClassifyBatchUseCase:

    if document_structure_analyzer is None:
        if extracted_asset_reader is None:
            raise ValueError(
                "extracted_asset_reader is required when document_structure_analyzer is not provided",
            )
        document_structure_analyzer = (
            create_document_structure_analyzer(
                session=session,
                extracted_asset_reader=extracted_asset_reader,
            )
        )

    return ClassifyBatchUseCase(
        task_repository=ClassificationTaskRepositoryImpl(
            session=session,
        ),
        chunk_reader=chunk_reader,
        document_structure_analyzer=document_structure_analyzer,
        classification_engine=(
            LLMClassificationEngine(
                prompt_provider=create_prompt_provider(
                    session,
                ),
                llm_gateway=create_llm_gateway(
                    session,
                ),
            )
        ),
        classification_repository=(
            ChunkClassificationRepositoryImpl(
                session=session,
            )
        ),
        batch_finalizer=batch_finalizer,
        knowledge_writer=create_knowledge_writer(
            session,
        ),
        ingestion_config_service=(
            create_ingestion_config_service(
                session,
            )
        ),
        uow=SQLAlchemyUnitOfWork(
            session=session,
        ),
        max_attempts=max_attempts,
    )


def create_document_structure_analyzer(
    *,
    extracted_asset_reader: ExtractedAssetReader,
    prompt_provider=None,
    llm_gateway=None,
    session=None,
) -> LLMDocumentStructureAnalyzer:

    if prompt_provider is None:
        if session is None:
            raise ValueError(
                "session is required when prompt_provider is not provided",
            )
        prompt_provider = create_prompt_provider(
            session,
        )

    if llm_gateway is None:
        if session is None:
            raise ValueError(
                "session is required when llm_gateway is not provided",
            )
        llm_gateway = create_llm_gateway(
            session,
        )

    return LLMDocumentStructureAnalyzer(
        extracted_asset_reader=extracted_asset_reader,
        prompt_provider=prompt_provider,
        llm_gateway=llm_gateway,
    )


@asynccontextmanager
async def create_classify_batch_use_case_scope(
    *,
    session_factory,
    chunk_reader: ChunkReader,
    extracted_asset_reader: ExtractedAssetReader,
    batch_finalizer: BatchFinalizer,
    max_attempts: int = 3,
) -> AsyncIterator[ClassifyBatchUseCase]:

    async with session_factory() as session:
        yield create_classify_batch_use_case(
            session=session,
            chunk_reader=chunk_reader,
            extracted_asset_reader=extracted_asset_reader,
            batch_finalizer=batch_finalizer,
            max_attempts=max_attempts,
        )
