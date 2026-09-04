import asyncio
import json
import logging
from typing import AsyncContextManager
from collections.abc import Callable
from uuid import UUID

from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)
from module.ingest.discovery.application.use_cases.discover_batch import (
    DiscoverBatchUseCase,
)


logger = logging.getLogger(__name__)


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

        logger.info("discovery started")

        while True:

            try:
                messages = await (
                    self.queue_client.receive_messages(
                        max_message_count=1,
                        max_wait_time=5,
                    )
                )

            except Exception:
                logger.exception(
                    "discovery receive_failed"
                )
                await asyncio.sleep(
                    5
                )
                continue

            for message in messages:

                try:
                    payload = json.loads(
                        str(message)
                    )
                    logger.info(
                        "discovery received payload=%s",
                        payload,
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
                        logger.info(
                            "discovery batch_start job_id=%s batch_size=%s",
                            request.ingestion_job_id,
                            request.batch_size,
                        )
                        response = (
                            await use_case.execute(
                                request
                            )
                        )
                        logger.info(
                            "discovery batch_done job_id=%s items=%s has_more=%s",
                            request.ingestion_job_id,
                            len(response.items),
                            response.has_more,
                        )

                    # còn Discovery workload
                    if response.has_more:
                        logger.info(
                            "discovery redispatch job_id=%s batch_size=%s",
                            request.ingestion_job_id,
                            request.batch_size,
                        )
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
                    logger.info(
                        "discovery completed job_id=%s",
                        request.ingestion_job_id,
                    )

                except Exception:
                    logger.exception(
                        "discovery failed"
                    )
                    continue

            await asyncio.sleep(
                1
            )
