import asyncio
import json
from uuid import UUID

from module.ingest.discovery.application.dtos.requests.discover_batch_request import (
    DiscoverBatchRequest,
)


class DiscoveryWorker:

    def __init__(
        self,
        queue_client,
        use_case,
        discovery_dispatcher,
    ):
        self.queue_client = queue_client
        self.use_case = use_case
        self.discovery_dispatcher = (
            discovery_dispatcher
        )

    async def run(
        self,
    ) -> None:

        while True:

            messages = (
                self.queue_client.receive_messages(
                    messages_per_page=1,
                )
            )

            async for message in messages:

                try:
                    payload = json.loads(
                        message.content
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

                    response = (
                        await self.use_case.execute(
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
                        .delete_message(
                            message.id,
                            message.pop_receipt,
                        )
                    )

                except Exception:
                    # Không delete message.
                    # Azure Queue sẽ visible lại
                    # sau visibility timeout.
                    raise

            await asyncio.sleep(
                1
            )