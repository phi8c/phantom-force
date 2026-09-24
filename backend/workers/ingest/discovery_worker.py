import asyncio
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
from shared.messaging.contracts import MessageConsumer
from workers.ingest.message_settlement import nack_with_backoff


logger = logging.getLogger(__name__)


class DiscoveryWorker:

    def __init__(
        self,
        consumer: MessageConsumer,
        use_case_factory: Callable[
            [],
            AsyncContextManager[
                DiscoverBatchUseCase
            ],
        ],
        discovery_dispatcher,
    ):
        self.consumer = consumer
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
                    self.consumer.receive(
                        max_messages=1,
                        wait_timeout=5,
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
                    payload = message.payload
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
                        message.ack()
                    )
                    logger.info(
                        "discovery completed job_id=%s",
                        request.ingestion_job_id,
                    )

                except Exception:
                    logger.exception(
                        "discovery failed"
                    )
                    await nack_with_backoff(
                        message,
                        logger=logger,
                        worker_name="discovery",
                    )
                    continue

            await asyncio.sleep(
                1
            )
