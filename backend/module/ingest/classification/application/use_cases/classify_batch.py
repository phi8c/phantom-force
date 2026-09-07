import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from module.ingest.knowledge.composition import (
    KnowledgeWriteRequest,
    KnowledgeWriter,
)
from module.ingest.classification.domain.contracts.batch_finalizer import (
    BatchFinalizer,
)
from module.ingest.classification.domain.contracts.chunk_classification_repository import (
    ChunkClassificationRepository,
)
from module.ingest.classification.domain.contracts.chunk_reader import (
    ChunkReader,
)
from module.ingest.classification.domain.contracts.classification_engine import (
    ClassificationEngine,
)
from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationTaskRepository,
)
from module.ingest.classification.domain.contracts.unit_of_work import (
    UnitOfWork,
)
from module.ingest.classification.domain.entities.chunk_classification import (
    ChunkClassification,
)
from module.ingest.classification.domain.enums.task_status import (
    TaskStatus,
)


logger = logging.getLogger(__name__)


class ClassifyBatchUseCase:

    def __init__(
        self,
        *,
        task_repository: ClassificationTaskRepository,
        chunk_reader: ChunkReader,
        classification_engine: ClassificationEngine,
        classification_repository: ChunkClassificationRepository,
        batch_finalizer: BatchFinalizer,
        knowledge_writer: KnowledgeWriter,
        uow: UnitOfWork,
        max_attempts: int = 3,
    ):
        self.task_repository = task_repository
        self.chunk_reader = chunk_reader
        self.classification_engine = classification_engine
        self.classification_repository = (
            classification_repository
        )
        self.batch_finalizer = batch_finalizer
        self.knowledge_writer = knowledge_writer
        self.uow = uow
        self.max_attempts = max_attempts

    async def execute(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Classification task not found"
            )

        if task.status == TaskStatus.SKIPPED:
            logger.info(
                "classification skipped task_id=%s",
                task_id,
            )
            await self._complete_skipped(
                task_id,
            )
            return

        if task.status != TaskStatus.PROCESSING:
            raise ValueError(
                "Classification task must be PROCESSING"
            )

        try:
            logger.info(
                "classification usecase_start task_id=%s job_id=%s batch_id=%s",
                task_id,
                task.ingestion_job_id,
                task.batch_id,
            )

            chunks = await self.chunk_reader.list_by_batch_id(
                task.batch_id,
            )
            logger.info(
                "classification chunks_loaded task_id=%s chunks=%s",
                task_id,
                len(chunks),
            )

            logger.info(
                "classification engine_start task_id=%s chunks=%s",
                task_id,
                len(chunks),
            )
            results = await (
                self.classification_engine
                .classify_batch(
                    chunks,
                )
            )
            logger.info(
                "classification engine_done task_id=%s results=%s",
                task_id,
                len(results),
            )

            classifications = [
                ChunkClassification(
                    id=None,
                    chunk_id=result.chunk_id,
                    model_name=result.model_name,
                    label=self._label_from_raw_response(
                        result.raw_response,
                    ),
                    confidence=(
                        self._confidence_from_raw_response(
                            result.raw_response,
                        )
                    ),
                    raw_response=result.raw_response,
                    created_at=None,
                )
                for result in results
            ]

            logger.info(
                "classification persist_start task_id=%s classifications=%s",
                task_id,
                len(classifications),
            )
            await self.classification_repository.upsert_many(
                classifications,
            )
            logger.info(
                "classification persist_done task_id=%s classifications=%s",
                task_id,
                len(classifications),
            )

            logger.info(
                "classification knowledge_persist_start task_id=%s results=%s",
                task_id,
                len(results),
            )
            for result in results:
                if result.raw_response is None:
                    continue

                await self.knowledge_writer.write(
                    KnowledgeWriteRequest(
                        ingestion_job_id=(
                            task.ingestion_job_id
                        ),
                        document_id=task.document_id,
                        chunk_id=result.chunk_id,
                        model_name=result.model_name,
                        raw_response=result.raw_response,
                    )
                )
            logger.info(
                "classification knowledge_persist_done task_id=%s results=%s",
                task_id,
                len(results),
            )

            signal = (
                await self.batch_finalizer
                .complete_classification(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    batch_id=task.batch_id,
                )
            )

            task.status = TaskStatus.COMPLETED
            task.claimed_by = None
            task.lease_until = None
            task.error = None
            task.completed_at = datetime.now(
                timezone.utc,
            )

            await self.task_repository.update(
                task,
            )

            logger.info(
                "classification commit task_id=%s",
                task_id,
            )
            await self.uow.commit()

            if signal.dispatch_index:
                logger.info(
                    "classification dispatch_index job_id=%s",
                    task.ingestion_job_id,
                )
                await self.batch_finalizer.dispatch_index(
                    task.ingestion_job_id,
                )

        except Exception as exc:
            logger.exception(
                "classification failed task_id=%s error=%s",
                task_id,
                exc,
            )
            await self.uow.rollback()

            task = await self.task_repository.get_by_id(
                task_id,
            )

            if task is not None:
                if (
                    task.attempt_count
                    >= self.max_attempts
                ):
                    task.status = TaskStatus.FAILED
                else:
                    task.status = TaskStatus.READY

                task.claimed_by = None
                task.lease_until = None
                task.error = str(exc)

                await self.task_repository.update(
                    task,
                )

                await self.uow.commit()

                logger.info(
                    "classification retry_state task_id=%s status=%s",
                    task_id,
                    task.status.value,
                )

            raise

    @staticmethod
    def _label_from_raw_response(
        raw_response: dict[str, Any] | None,
    ) -> str:

        classification = (
            ClassifyBatchUseCase
            ._classification_payload(
                raw_response,
            )
        )

        label = classification.get("label")

        if label is None:
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        return str(label)

    @staticmethod
    def _confidence_from_raw_response(
        raw_response: dict[str, Any] | None,
    ) -> float | None:

        classification = (
            ClassifyBatchUseCase
            ._classification_payload(
                raw_response,
            )
        )

        confidence = classification.get("confidence")

        if confidence is None:
            return None

        value = float(confidence)
        if value < 0 or value > 1:
            raise ValueError(
                "Classification confidence must be between 0 and 1",
            )

        return value

    @staticmethod
    def _classification_payload(
        raw_response: dict[str, Any] | None,
    ) -> dict[str, Any]:

        if raw_response is None:
            return {}

        classification = raw_response.get(
            "classification",
        )

        if isinstance(
            classification,
            dict,
        ):
            return classification

        return raw_response

    async def _complete_skipped(
        self,
        task_id: UUID,
    ) -> None:

        task = await self.task_repository.get_by_id(
            task_id,
        )

        if task is None:
            raise ValueError(
                "Classification task not found"
            )

        signal = (
            await self.batch_finalizer
            .complete_classification(
                ingestion_job_id=task.ingestion_job_id,
                batch_id=task.batch_id,
            )
        )

        logger.info(
            "classification skipped_commit task_id=%s",
            task_id,
        )
        await self.uow.commit()

        if signal.dispatch_index:
            logger.info(
                "classification skipped_dispatch_index job_id=%s",
                task.ingestion_job_id,
            )
            await self.batch_finalizer.dispatch_index(
                task.ingestion_job_id,
            )
