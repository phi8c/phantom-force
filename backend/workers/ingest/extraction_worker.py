import asyncio
import json
import socket
from typing import AsyncContextManager
from collections.abc import Callable
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID

from module.ingest.extraction.application.use_cases.extract_document import (
    ExtractDocumentUseCase,
)


class ExtractionWorker:

    def __init__(
        self,
        queue_client,
        claim_scope_factory,
        use_case_factory: Callable[
            [],
            AsyncContextManager[
                ExtractDocumentUseCase
            ],
        ],
        claim_size: int = 20,
        lease_seconds: int = 300,
        max_concurrency: int = 5,
    ):
        self.queue_client = queue_client
        self.claim_scope_factory = (
            claim_scope_factory
        )
        self.use_case_factory = use_case_factory
        self.claim_size = claim_size
        self.lease_seconds = lease_seconds
        self.semaphore = asyncio.Semaphore(
            max_concurrency
        )
        self.worker_id = socket.gethostname()

    async def run(
        self,
    ) -> None:

        while True:
            messages = await (
                self.queue_client.receive_messages(
                    max_message_count=1,
                    max_wait_time=5,
                )
            )

            found_message = bool(messages)

            for message in messages:
                try:
                    payload = json.loads(
                        str(message)
                    )

                    ingestion_job_id = UUID(
                        payload[
                            "ingestion_job_id"
                        ]
                    )

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
                        task_repository, uow = claim_scope

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

                    await (
                        self.queue_client
                        .complete_message(
                            message,
                        )
                    )

                except Exception:
                    continue

            if not found_message:
                await asyncio.sleep(1)

    async def _process(
        self,
        task_id: UUID,
    ) -> None:

        async with self.semaphore:
            async with self.use_case_factory() as use_case:
                await use_case.execute(
                    task_id,
                )
