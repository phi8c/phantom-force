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
    max_attempts: int = 3,
) -> ClassifyBatchUseCase:

    return ClassifyBatchUseCase(
        task_repository=ClassificationTaskRepositoryImpl(
            session=session,
        ),
        chunk_reader=chunk_reader,
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


@asynccontextmanager
async def create_classify_batch_use_case_scope(
    *,
    session_factory,
    chunk_reader: ChunkReader,
    batch_finalizer: BatchFinalizer,
    max_attempts: int = 3,
) -> AsyncIterator[ClassifyBatchUseCase]:

    async with session_factory() as session:
        yield create_classify_batch_use_case(
            session=session,
            chunk_reader=chunk_reader,
            batch_finalizer=batch_finalizer,
            max_attempts=max_attempts,
        )
