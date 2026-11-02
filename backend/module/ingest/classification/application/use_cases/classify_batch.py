import logging
from datetime import datetime
from datetime import timezone
from datetime import timedelta
from typing import Any
from uuid import UUID

from module.ingest.config.composition import (
    IngestionConfigService,
)
from module.ingest.knowledge.composition import (
    KnowledgeDocumentContext,
    KnowledgeDocumentTypeContext,
    KnowledgeHeadContext,
    KnowledgeTopicContext,
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
from module.ingest.classification.domain.contracts.document_structure_analyzer import (
    DocumentStructureAnalyzer,
)
from module.ingest.classification.domain.contracts.classification_task_repository import (
    ClassificationLeaseLostError,
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
from module.ingest.orchestration.application.services import (
    NoOpOrchestrationProgressService,
)
from module.ingest.orchestration.application.services import (
    OrchestrationProgressService,
)
from module.ingest.orchestration.domain.enums import IngestionStage


logger = logging.getLogger(__name__)


class ClassifyBatchUseCase:

    def __init__(
        self,
        *,
        task_repository: ClassificationTaskRepository,
        chunk_reader: ChunkReader,
        document_structure_analyzer: DocumentStructureAnalyzer,
        classification_engine: ClassificationEngine,
        classification_repository: ChunkClassificationRepository,
        batch_finalizer: BatchFinalizer,
        knowledge_writer: KnowledgeWriter,
        ingestion_config_service: IngestionConfigService,
        uow: UnitOfWork,
        orchestration_progress_service: (
            OrchestrationProgressService
            | NoOpOrchestrationProgressService
            | None
        ) = None,
        max_attempts: int = 3,
        page_size: int = 32,
    ):
        self.task_repository = task_repository
        self.chunk_reader = chunk_reader
        self.document_structure_analyzer = (
            document_structure_analyzer
        )
        self.classification_engine = classification_engine
        self.classification_repository = (
            classification_repository
        )
        self.batch_finalizer = batch_finalizer
        self.knowledge_writer = knowledge_writer
        self.ingestion_config_service = (
            ingestion_config_service
        )
        self.orchestration_progress_service = (
            orchestration_progress_service
            or NoOpOrchestrationProgressService()
        )
        self.uow = uow
        self.max_attempts = max_attempts
        if not 1 <= page_size <= 1000:
            raise ValueError('Classification page size must be between 1 and 1000')
        self.page_size = page_size

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

        original_owner = task.claimed_by
        try:
            logger.info(
                "classification usecase_start task_id=%s job_id=%s batch_id=%s",
                task_id,
                task.ingestion_job_id,
                task.batch_id,
            )

            ingestion_job = await self.ingestion_config_service.get_job(task.ingestion_job_id)
            if ingestion_job is None:
                raise ValueError('Ingestion job not found')
            document_context = await self.document_structure_analyzer.analyze(
                ingestion_job_id=task.ingestion_job_id, document_id=task.document_id,
            )
            processed = 0
            async for chunks in self.chunk_reader.iter_by_batch_id(task.batch_id, page_size=self.page_size):
                await self._classify_page(task, ingestion_job, document_context, chunks)
                processed += len(chunks)
            if not processed:
                raise ValueError('Cannot classify an empty chunk batch')
            logger.info('classification chunks_processed task_id=%s chunks=%s', task_id, processed)

            signal = (
                await self.batch_finalizer
                .complete_classification(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    batch_id=task.batch_id,
                )
            )

            if original_owner is not None:
                owned = await self.task_repository.renew_lease(
                    task_id, claimed_by=original_owner,
                    lease_until=datetime.now(timezone.utc) + timedelta(seconds=300),
                )
                if not owned:
                    raise ClassificationLeaseLostError('Cannot complete classification after losing its lease')
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

            await (
                self.orchestration_progress_service
                .mark_stage_completed(
                    ingestion_job_id=(
                        task.ingestion_job_id
                    ),
                    document_id=task.document_id,
                    stage=IngestionStage.CLASSIFICATION,
                )
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

        except ClassificationLeaseLostError:
            await self.uow.rollback()
            raise
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
                if task.status != TaskStatus.PROCESSING or task.claimed_by != original_owner:
                    raise
                if original_owner is not None and not await self.task_repository.renew_lease(
                    task_id, claimed_by=original_owner,
                    lease_until=datetime.now(timezone.utc) + timedelta(seconds=300),
                ):
                    await self.uow.rollback()
                    raise
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

                if task.status == TaskStatus.FAILED:
                    await (
                        self.orchestration_progress_service
                        .mark_stage_failed(
                            ingestion_job_id=(
                                task.ingestion_job_id
                            ),
                            document_id=task.document_id,
                            stage=(
                                IngestionStage
                                .CLASSIFICATION
                            ),
                            error=str(exc),
                        )
                    )
                else:
                    await (
                        self.orchestration_progress_service
                        .mark_stage_ready(
                            ingestion_job_id=(
                                task.ingestion_job_id
                            ),
                            document_id=task.document_id,
                            stage=(
                                IngestionStage
                                .CLASSIFICATION
                            ),
                        )
                    )

                await self.uow.commit()

                logger.info(
                    "classification retry_state task_id=%s status=%s",
                    task_id,
                    task.status.value,
                )

            raise

    async def _classify_page(self, task, ingestion_job, document_context, chunks):
        if not chunks or any(not chunk.content.strip() for chunk in chunks):
            raise ValueError('Classification page must contain readable chunks')
        by_id = {chunk.id: chunk for chunk in chunks}
        if len(by_id) != len(chunks):
            raise ValueError('Duplicate input chunks')
        results = await self.classification_engine.classify_batch(chunks, document_context=document_context)
        result_ids = [result.chunk_id for result in results]
        if len(result_ids) != len(by_id) or set(result_ids) != set(by_id):
            raise ValueError('Classification must return exactly one result for every input chunk')
        classifications = []
        for result in results:
            self._validate_response_contract(result.raw_response, task_id=task.id, chunk_id=result.chunk_id)
            if not result.raw_response['information']:
                logger.warning('classification no_information task_id=%s chunk_id=%s', task.id, result.chunk_id)
            classifications.append(ChunkClassification(
                id=None, chunk_id=result.chunk_id, model_name=result.model_name,
                label=self._sensitivity_level_from_raw_response(
                    result.raw_response, task_id=task.id, chunk_id=result.chunk_id),
                confidence=None, raw_response=result.raw_response, created_at=None,
            ))
        await self.classification_repository.upsert_many(classifications)
        context = self._knowledge_document_context(document_context)
        for result in results:
            await self.knowledge_writer.write(KnowledgeWriteRequest(
                knowledge_space_id=ingestion_job.knowledge_space_id,
                document_id=task.document_id, chunk_id=result.chunk_id, model_name=result.model_name,
                raw_response=result.raw_response, document_context=context,
                source_metadata=by_id[result.chunk_id].metadata,
            ))

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
            "objects": list,
            "information_types": list,
            "information_fields": list,
            "information": list,
        }

        for key, expected_type in required_types.items():
            if key not in raw_response:
                logger.error(
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s",
                    task_id,
                    chunk_id,
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
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s expected_type=%s actual_type=%s",
                    task_id,
                    chunk_id,
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
            "information",
        ):
            for item in raw_response[key]:
                if not isinstance(item, dict):
                    logger.error(
                        "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s",
                        task_id,
                        chunk_id,
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
                    "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s",
                    task_id,
                    chunk_id,
                    "invalid_field_type",
                    "information.information_type",
                )
                raise ValueError(
                    "Classification response "
                    "information.information_type must be string",
                )

            for ref_field in (
                "object_refs",
            ):
                refs = item.get(ref_field)
                if refs is None:
                    continue
                if not isinstance(refs, list):
                    logger.error(
                        "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s",
                        task_id,
                        chunk_id,
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
                            "classification structured_knowledge_parse_failed task_id=%s chunk_id=%s reason=%s field=%s",
                            task_id,
                            chunk_id,
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
                "classification sensitivity_missing task_id=%s chunk_id=%s reason=%s",
                task_id,
                chunk_id,
                "raw_response_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        if "sensitivity" not in raw_response:
            logger.error(
                "classification sensitivity_missing task_id=%s chunk_id=%s reason=%s",
                task_id,
                chunk_id,
                "field_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        sensitivity = raw_response["sensitivity"]
        if not isinstance(sensitivity, dict):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s reason=%s",
                task_id,
                chunk_id,
                "sensitivity_not_object",
            )
            raise ValueError(
                "Classification response sensitivity must be an object",
            )

        if "level" not in sensitivity:
            logger.error(
                "classification sensitivity_missing task_id=%s chunk_id=%s reason=%s",
                task_id,
                chunk_id,
                "level_missing",
            )
            raise ValueError(
                "Classification response missing sensitivity label",
            )

        level = sensitivity["level"]
        if isinstance(level, bool) or not isinstance(level, int):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s reason=%s level=%s",
                task_id,
                chunk_id,
                "level_not_integer",
                level,
            )
            raise ValueError(
                "Classification sensitivity level must be an integer",
            )

        if level < 1:
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s reason=%s level=%s",
                task_id,
                chunk_id,
                "level_out_of_range",
                level,
            )
            raise ValueError(
                "Classification sensitivity level must be at least 1",
            )

        description = sensitivity.get("description")
        if not isinstance(description, str):
            logger.error(
                "classification sensitivity_parse_failed task_id=%s chunk_id=%s reason=%s description=%s",
                task_id,
                chunk_id,
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

        await (
            self.orchestration_progress_service
            .mark_stage_skipped(
                ingestion_job_id=task.ingestion_job_id,
                document_id=task.document_id,
                stage=IngestionStage.CLASSIFICATION,
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

    @staticmethod
    def _knowledge_document_context(
        document_context,
    ) -> KnowledgeDocumentContext:

        return KnowledgeDocumentContext(
            document_type=KnowledgeDocumentTypeContext(
                code=document_context.document_type.code,
                name=document_context.document_type.name,
                description=(
                    document_context.document_type.description
                ),
                metadata=document_context.document_type.metadata,
            ),
            topic=KnowledgeTopicContext(
                code=document_context.topic.code,
                name=document_context.topic.name,
                description=document_context.topic.description,
                metadata=document_context.topic.metadata,
            ),
            head=KnowledgeHeadContext(
                type=document_context.head.type,
                code=document_context.head.code,
                name=document_context.head.name,
                description=document_context.head.description,
                metadata=document_context.head.metadata,
            ),
        )
