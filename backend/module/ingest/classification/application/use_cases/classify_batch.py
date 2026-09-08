import logging
from datetime import datetime
from datetime import timezone
from typing import Any
from uuid import UUID

from module.ingest.config.composition import (
    IngestionConfigService,
)
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
        ingestion_config_service: IngestionConfigService,
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
        self.ingestion_config_service = (
            ingestion_config_service
        )
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

            classifications = []
            for result in results:
                self._validate_response_contract(
                    result.raw_response,
                    task_id=task.id,
                    chunk_id=result.chunk_id,
                )
                classifications.append(
                    ChunkClassification(
                        id=None,
                        chunk_id=result.chunk_id,
                        model_name=result.model_name,
                        label=self._sensitivity_level_from_raw_response(
                            result.raw_response,
                            task_id=task.id,
                            chunk_id=result.chunk_id,
                        ),
                        confidence=None,
                        raw_response=result.raw_response,
                        created_at=None,
                    )
                )

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
            ingestion_job = await (
                self.ingestion_config_service.get_job(
                    task.ingestion_job_id,
                )
            )

            if ingestion_job is None:
                raise ValueError(
                    "Ingestion job not found",
                )

            for result in results:
                if result.raw_response is None:
                    continue

                try:
                    await self.knowledge_writer.write(
                        KnowledgeWriteRequest(
                            knowledge_space_id=(
                                ingestion_job
                                .knowledge_space_id
                            ),
                            document_id=task.document_id,
                            chunk_id=result.chunk_id,
                            model_name=result.model_name,
                            raw_response=result.raw_response,
                        )
                    )
                except Exception as exc:
                    logger.error(
                        "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s error=%s",
                        task.id,
                        result.chunk_id,
                        result.raw_response,
                        exc,
                    )
                    raise
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
    def _sensitivity_level_from_raw_response(
        raw_response: dict[str, Any] | None,
        *,
        task_id: UUID | None = None,
        chunk_id: UUID | None = None,
    ) -> str:

        sensitivity = ClassifyBatchUseCase._sensitivity(
            raw_response,
            task_id=task_id,
            chunk_id=chunk_id,
        )

        level = sensitivity["level"]

        return str(level)

    @staticmethod
    def _validate_response_contract(
        raw_response: dict[str, Any] | None,
        *,
        task_id: UUID | None = None,
        chunk_id: UUID | None = None,
    ) -> None:

        ClassifyBatchUseCase._sensitivity(
            raw_response,
            task_id=task_id,
            chunk_id=chunk_id,
        )

        if raw_response is None:
            return

        required_types = {
            "document_type": dict,
            "objects": list,
            "information_types": list,
            "information_fields": list,
            "topics": list,
            "information": list,
        }

        for key, expected_type in required_types.items():
            if key not in raw_response:
                logger.error(
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s",
                    task_id,
                    chunk_id,
                    raw_response,
                    "field_missing",
                    key,
                )
                raise ValueError(
                    f"Classification response missing {key}",
                )
            if not isinstance(
                raw_response[key],
                expected_type,
            ):
                logger.error(
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s expected_type=%s actual_type=%s",
                    task_id,
                    chunk_id,
                    raw_response,
                    "invalid_field_type",
                    key,
                    expected_type.__name__,
                    type(raw_response[key]).__name__,
                )
                raise ValueError(
                    "Classification response field "
                    f"{key} must be {expected_type.__name__}",
                )

        for key in (
            "objects",
            "information_types",
            "information_fields",
            "topics",
            "information",
        ):
            for item in raw_response[key]:
                if not isinstance(item, dict):
                    logger.error(
                        "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s",
                        task_id,
                        chunk_id,
                        raw_response,
                        "array_item_not_object",
                        key,
                    )
                    raise ValueError(
                        "Classification response "
                        f"{key} items must be objects",
                    )

        for item in raw_response["information"]:
            information_type = item.get("information_type")
            if (
                information_type is not None
                and not isinstance(information_type, str)
            ):
                logger.error(
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s",
                    task_id,
                    chunk_id,
                    raw_response,
                    "invalid_field_type",
                    "information.information_type",
                )
                raise ValueError(
                    "Classification response "
                    "information.information_type must be string",
                )

            for ref_field in (
                "object_refs",
                "topic_refs",
            ):
                refs = item.get(ref_field)
                if refs is None:
                    continue
                if not isinstance(refs, list):
                    logger.error(
                        "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s",
                        task_id,
                        chunk_id,
                        raw_response,
                        "invalid_field_type",
                        f"information.{ref_field}",
                    )
                    raise ValueError(
                        "Classification response "
                        f"information.{ref_field} must be a list",
                    )
                for ref in refs:
                    if not isinstance(ref, str):
                        logger.error(
                            "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s field=%s",
                            task_id,
                            chunk_id,
                            raw_response,
                            "array_item_not_string",
                            f"information.{ref_field}",
                        )
                        raise ValueError(
                            "Classification response "
                            f"information.{ref_field} items must be strings",
                        )

    @staticmethod
    def _sensitivity(
        raw_response: dict[str, Any] | None,
        *,
        task_id: UUID | None = None,
        chunk_id: UUID | None = None,
    ) -> dict[str, Any]:

        if raw_response is None:
            logger.error(
                "classification sensitivity_missing task_id=%s chunk_id=%s raw_response=%s reason=%s",
                task_id,
                chunk_id,
                raw_response,
                "raw_response_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        if "sensitivity" not in raw_response:
            logger.error(
                "classification sensitivity_missing task_id=%s chunk_id=%s raw_response=%s reason=%s",
                task_id,
                chunk_id,
                raw_response,
                "field_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        sensitivity = raw_response["sensitivity"]
        if not isinstance(sensitivity, dict):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s",
                task_id,
                chunk_id,
                raw_response,
                "sensitivity_not_object",
            )
            raise ValueError(
                "Classification response sensitivity must be an object",
            )

        if "level" not in sensitivity:
            logger.error(
                "classification sensitivity_missing task_id=%s chunk_id=%s raw_response=%s reason=%s",
                task_id,
                chunk_id,
                raw_response,
                "level_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        level = sensitivity["level"]
        if isinstance(level, bool) or not isinstance(level, int):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s level=%s",
                task_id,
                chunk_id,
                raw_response,
                "level_not_integer",
                level,
            )
            raise ValueError(
                "Classification sensitivity level must be an integer",
            )

        if level < 1:
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s level=%s",
                task_id,
                chunk_id,
                raw_response,
                "level_out_of_range",
                level,
            )
            raise ValueError(
                "Classification sensitivity level must be at least 1",
            )

        description = sensitivity.get("description")
        if not isinstance(description, str):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s raw_response=%s reason=%s description=%s",
                task_id,
                chunk_id,
                raw_response,
                "description_not_string",
                description,
            )
            raise ValueError(
                "Classification sensitivity description must be a string",
            )

        return sensitivity

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
