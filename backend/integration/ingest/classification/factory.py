from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from module.ingest.classification.application.use_cases.classify_batch import (
    ClassifyBatchUseCase,
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

from integration.ingest.classification.batch_finalizer import (
    ModuleBatchFinalizer,
)
from integration.ingest.classification.chunk_reader import (
    ModuleChunkReader,
)
from integration.ingest.classification.legacy_classification_engine import (
    LegacyClassificationEngineAdapter,
)


def create_classify_batch_use_case(
    *,
    session: AsyncSession,
    max_attempts: int = 3,
) -> ClassifyBatchUseCase:

    return ClassifyBatchUseCase(
        task_repository=ClassificationTaskRepositoryImpl(
            session=session,
        ),
        chunk_reader=ModuleChunkReader(
            session=session,
        ),
        classification_engine=(
            LegacyClassificationEngineAdapter()
        ),
        classification_repository=(
            ChunkClassificationRepositoryImpl(
                session=session,
            )
        ),
        batch_finalizer=ModuleBatchFinalizer(
            session=session,
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
    max_attempts: int = 3,
) -> AsyncIterator[ClassifyBatchUseCase]:

    async with session_factory() as session:
        yield create_classify_batch_use_case(
            session=session,
            max_attempts=max_attempts,
        )
