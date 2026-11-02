import asyncio
import logging
import socket
from typing import AsyncContextManager
from collections.abc import Callable
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from module.ingest.classification.application.use_cases.classify_batch import (
    ClassifyBatchUseCase,
)
from module.ingest.orchestration.domain.enums import IngestionStage
from shared.messaging.contracts import MessageConsumer
from workers.ingest.message_settlement import nack_with_backoff
from workers.ingest.task_lease import execute_with_lease


logger = logging.getLogger(__name__)


class ClassificationWorker:

    def __init__(
        self,
        consumer: MessageConsumer,
        claim_scope_factory,
        use_case_factory: Callable[
            [],
            AsyncContextManager[
                ClassifyBatchUseCase
            ],
        ],
        claim_size: int = 1,
        lease_seconds: int = 300,
        max_concurrency: int = 1,
    ):
        self.consumer = consumer
        self.claim_scope_factory = (
            claim_scope_factory
        )
        self.use_case_factory = use_case_factory
        if min(claim_size, max_concurrency, lease_seconds) < 1:
            raise ValueError('Worker limits must be positive')
        self.claim_size = min(claim_size, max_concurrency)
        self.lease_seconds = lease_seconds
        self.semaphore = asyncio.Semaphore(
            max_concurrency
        )
        self.worker_id = f'{socket.gethostname()}:{uuid4()}'

    async def run(
        self,
    ) -> None:

        logger.info(
            "classification started worker_id=%s claim_size=%s lease_seconds=%s",
            self.worker_id,
            self.claim_size,
            self.lease_seconds,
        )

        while True:
            try:
                messages = await (
                    self.consumer.receive(
                        max_messages=1,
                        wait_timeout=5,
                    )
                )

            except Exception:
                logger.exception(
                    "classification receive_failed"
                )
                await asyncio.sleep(5)
                continue

            found_message = bool(messages)

            for message in messages:
                try:
                    payload = message.payload
                    logger.info(
                        "classification received payload=%s",
                        payload,
                    )

                    ingestion_job_id = UUID(
                        payload[
                            "ingestion_job_id"
                        ]
                    )

                    while True:
                        lease_until = (
                            datetime.now(
                                timezone.utc
                            )
                            + timedelta(
                                seconds=(
                                    self.lease_seconds
                                )
                            )
                        )

                        async with (
                            self.claim_scope_factory()
                        ) as claim_scope:
                            (
                                task_repository,
                                uow,
                                progress_service,
                            ) = claim_scope

                            tasks = (
                                await task_repository
                                .claim_ready(
                                    ingestion_job_id,
                                    limit=self.claim_size,
                                    claimed_by=(
                                        self.worker_id
                                    ),
                                    lease_until=lease_until,
                                )
                            )

                            await uow.commit()

                            for task in tasks:
                                await (
                                    progress_service
                                    .mark_stage_processing(
                                        ingestion_job_id=(
                                            task.ingestion_job_id
                                        ),
                                        document_id=(
                                            task.document_id
                                        ),
                                        stage=(
                                            IngestionStage
                                            .CLASSIFICATION
                                        ),
                                    )
                                )

                            await uow.commit()
                            logger.info(
                                "classification claimed job_id=%s tasks=%s",
                                ingestion_job_id,
                                len(tasks),
                            )

                        await asyncio.gather(
                            *[
                                self._process(
                                    task.id
                                )
                                for task in tasks
                                if task.id
                                is not None
                            ]
                        )
                        if not tasks:
                            async with self.claim_scope_factory() as scope:
                                repository, _, _ = scope
                                pending = await repository.has_unfinished(ingestion_job_id)
                            if not pending:
                                break
                            await asyncio.sleep(min(10, self.lease_seconds / 3))

                    await (
                        message.ack()
                    )
                    logger.info(
                        "classification completed job_id=%s",
                        ingestion_job_id,
                    )

                except Exception:
                    logger.exception(
                        "classification failed"
                    )
                    await nack_with_backoff(
                        message,
                        logger=logger,
                        worker_name="classification",
                    )
                    continue

            if not found_message:
                await asyncio.sleep(1)

    async def _process(
        self,
        task_id: UUID,
    ) -> None:

        async with self.semaphore:
            async with self.use_case_factory() as use_case:
                logger.info(
                    "classification task_start task_id=%s",
                    task_id,
                )
                await self._execute_with_heartbeat(use_case, task_id)
                logger.info(
                    "classification task_done task_id=%s",
                    task_id,
                )

    async def _execute_with_heartbeat(self, use_case, task_id):
        async def renew():
            async with self.claim_scope_factory() as scope:
                repository, uow, _ = scope
                renewed = await repository.renew_lease(
                    task_id, claimed_by=self.worker_id,
                    lease_until=datetime.now(timezone.utc) + timedelta(seconds=self.lease_seconds),
                )
                await uow.commit()
                return renewed

        async def completed():
            async with self.claim_scope_factory() as scope:
                repository, _, _ = scope
                current = await repository.get_by_id(task_id)
                return current is not None and current.status.value in {'COMPLETED', 'SKIPPED'}

        return await execute_with_lease(use_case.execute(task_id), renew=renew, completed=completed,
                                        interval=max(0.1, self.lease_seconds / 3))
