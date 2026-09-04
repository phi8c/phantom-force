from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

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

from module.ingest.classification.infrastructure.engine.legacy_classification_engine import (
    LegacyClassificationEngineAdapter,
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
            LegacyClassificationEngineAdapter()
        ),
        classification_repository=(
            ChunkClassificationRepositoryImpl(
                session=session,
            )
        ),
        batch_finalizer=batch_finalizer,
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
