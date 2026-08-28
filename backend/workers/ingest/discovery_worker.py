import asyncio
import json
from typing import AsyncContextManager
from collections.abc import Callable
from uuid import UUID

from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)
from module.ingest.discovery.application.use_cases.discover_batch import (
    DiscoverBatchUseCase,
)


class DiscoveryWorker:

    def __init__(
        self,
        queue_client,
        use_case_factory: Callable[
            [],
            AsyncContextManager[
                DiscoverBatchUseCase
            ],
        ],
        discovery_dispatcher,
    ):
        self.queue_client = queue_client
        self.use_case_factory = use_case_factory
        self.discovery_dispatcher = (
            discovery_dispatcher
        )

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

            for message in messages:

                try:
                    payload = json.loads(
                        str(message)
                    )

                    request = DiscoverBatchRequest(
                        ingestion_job_id=UUID(
                            payload[
                                "ingestion_job_id"
                            ]
                        ),
                        batch_size=int(
                            payload.get(
                                "batch_size",
                                100,
                            )
                        ),
                    )

                    async with (
                        self.use_case_factory()
                    ) as use_case:
                        response = (
                            await use_case.execute(
                                request
                            )
                        )

                    # còn Discovery workload
                    if response.has_more:
                        await (
                            self.discovery_dispatcher
                            .dispatch(
                                ingestion_job_id=(
                                    request.ingestion_job_id
                                ),
                                batch_size=(
                                    request.batch_size
                                ),
                            )
                        )

                    await (
                        self.queue_client
                        .complete_message(
                            message,
                        )
                    )

                except Exception:
                    # Không delete message.
                    # Azure Queue sẽ visible lại
                    # sau visibility timeout.
                    continue

            await asyncio.sleep(
                1
            )
