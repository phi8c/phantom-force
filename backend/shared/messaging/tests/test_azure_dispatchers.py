from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from shared.messaging.azure_service_bus.dispatchers import (
    AzureChunkingDispatcher,
    AzureClassificationDispatcher,
    AzureDiscoveryDispatcher,
    AzureDownloadDispatcher,
    AzureEmbeddingDispatcher,
    AzureExtractionDispatcher,
)
from shared.messaging.azure_service_bus.composition.factory import (
    create_azure_producer,
)


class FakeSender:
    def __init__(self) -> None:
        self.messages = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None

    async def send_messages(self, message) -> None:
        self.messages.append(message)


class FakeServiceBusClient:
    def __init__(self) -> None:
        self.senders = {}

    def get_queue_sender(self, *, queue_name: str) -> FakeSender:
        sender = self.senders.setdefault(queue_name, FakeSender())
        return sender


def payloads(client: FakeServiceBusClient) -> list[tuple[str, dict]]:
    result = []
    for queue_name, sender in client.senders.items():
        for message in sender.messages:
            result.append((queue_name, json.loads(str(message))))
    return result


class AzureDispatcherRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_producer_does_not_create_queue_receivers(self) -> None:
        client = MagicMock()
        client.close = AsyncMock()

        with patch(
            "shared.messaging.azure_service_bus.composition.factory.create_service_bus_client",
            return_value=client,
        ), patch(
            "shared.messaging.azure_service_bus.composition.factory._settings",
            return_value=SimpleNamespace(
                AZURE_SERVICE_BUS_QUEUE_NAME="discovery",
                AZURE_SERVICE_BUS_DOWNLOAD_QUEUE="download",
                AZURE_SERVICE_BUS_EXTRACT_QUEUE="extraction",
                AZURE_SERVICE_BUS_CHUNK_QUEUE="chunking",
                AZURE_SERVICE_BUS_EMBED_QUEUE="embedding",
                AZURE_SERVICE_BUS_CLASSIFY_QUEUE="classification",
            ),
        ):
            resources = await create_azure_producer()

        client.get_queue_receiver.assert_not_called()
        await resources.close()
        client.close.assert_awaited_once_with()

    async def test_all_azure_payloads_remain_unchanged(self) -> None:
        client = FakeServiceBusClient()
        job_id = UUID("11111111-2222-3333-4444-555555555555")

        await AzureDiscoveryDispatcher(
            client, "discovery-queue"
        ).dispatch(job_id, 25)
        await AzureDownloadDispatcher(
            client, "download-queue"
        ).dispatch(job_id)
        await AzureExtractionDispatcher(
            client, "extraction-queue"
        ).dispatch(job_id)
        await AzureChunkingDispatcher(
            client, "chunking-queue"
        ).dispatch(job_id)
        await AzureEmbeddingDispatcher(
            client, "embedding-queue"
        ).dispatch_job(job_id)
        await AzureClassificationDispatcher(
            client, "classification-queue"
        ).dispatch_job(job_id)

        common = {"ingestion_job_id": str(job_id)}
        self.assertEqual(
            payloads(client),
            [
                (
                    "discovery-queue",
                    {
                        "ingestion_job_id": str(job_id),
                        "batch_size": 25,
                    },
                ),
                ("download-queue", common),
                ("extraction-queue", common),
                ("chunking-queue", common),
                ("embedding-queue", common),
                ("classification-queue", common),
            ],
        )


if __name__ == "__main__":
    unittest.main()
