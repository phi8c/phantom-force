import asyncio
import json
import socket
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from uuid import UUID


class ChunkingWorker:

    def __init__(
        self,
        queue_client,
        task_repository,
        use_case,
        uow,
        claim_size: int = 20,
        lease_seconds: int = 300,
        max_concurrency: int = 5,
    ):
        self.queue_client = queue_client
        self.task_repository = task_repository
        self.use_case = use_case
        self.uow = uow
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
            messages = (
                self.queue_client.receive_messages(
                    messages_per_page=1,
                )
            )

            found_message = False

            async for message in messages:
                found_message = True

                try:
                    payload = json.loads(
                        message.content
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

                    tasks = (
                        await self.task_repository
                        .claim_ready(
                            ingestion_job_id,
                            limit=self.claim_size,
                            claimed_by=(
                                self.worker_id
                            ),
                            lease_until=lease_until,
                        )
                    )

                    await self.uow.commit()

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
                        .delete_message(
                            message.id,
                            message.pop_receipt,
                        )
                    )

                except Exception:
                    await self.uow.rollback()
                    continue

            if not found_message:
                await asyncio.sleep(1)

    async def _process(
        self,
        task_id: UUID,
    ) -> None:

        async with self.semaphore:
            await self.use_case.execute(
                task_id,
            )
