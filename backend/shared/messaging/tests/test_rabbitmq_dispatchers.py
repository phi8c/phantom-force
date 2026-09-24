from __future__ import annotations

import json
import unittest
from uuid import UUID

import aio_pika

from shared.messaging.rabbitmq.dispatchers import (
    RabbitMQChunkingDispatcher,
    RabbitMQClassificationDispatcher,
    RabbitMQDiscoveryDispatcher,
    RabbitMQDownloadDispatcher,
    RabbitMQEmbeddingDispatcher,
    RabbitMQExtractionDispatcher,
)
from shared.messaging.rabbitmq.publisher import RabbitMQPublisher


class FakeExchange:
    def __init__(self) -> None:
        self.published = []

    async def publish(self, message, *, routing_key: str) -> None:
        self.published.append((message, routing_key))


class FakePublisherChannel:
    def __init__(self) -> None:
        self.default_exchange = FakeExchange()
        self.declarations = []

    async def declare_queue(self, queue_name: str, **kwargs) -> None:
        self.declarations.append((queue_name, kwargs))


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls = []

    async def publish(self, queue_name: str, payload: dict) -> None:
        self.calls.append((queue_name, payload))


class RabbitMQPublisherTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_declares_once_and_sends_persistent_json(self) -> None:
        channel = FakePublisherChannel()
        publisher = RabbitMQPublisher(channel)
        payload = {"ingestion_job_id": "job"}

        await publisher.publish("download-queue", payload)
        await publisher.publish("download-queue", payload)

        self.assertEqual(
            channel.declarations,
            [
                (
                    "download-queue",
                    {
                        "durable": True,
                        "auto_delete": False,
                        "exclusive": False,
                    },
                )
            ],
        )
        message, routing_key = channel.default_exchange.published[0]
        self.assertEqual(routing_key, "download-queue")
        self.assertEqual(json.loads(message.body.decode("utf-8")), payload)
        self.assertEqual(message.content_type, "application/json")
        self.assertEqual(message.content_encoding, "utf-8")
        self.assertEqual(
            message.delivery_mode,
            aio_pika.DeliveryMode.PERSISTENT,
        )


class RabbitMQDispatcherTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_dispatchers_preserve_azure_payload_contracts(self) -> None:
        publisher = RecordingPublisher()
        job_id = UUID("11111111-2222-3333-4444-555555555555")

        await RabbitMQDiscoveryDispatcher(
            publisher, "discovery-queue"
        ).dispatch(job_id, 25)
        await RabbitMQDownloadDispatcher(
            publisher, "download-queue"
        ).dispatch(job_id)
        await RabbitMQExtractionDispatcher(
            publisher, "extraction-queue"
        ).dispatch(job_id)
        await RabbitMQChunkingDispatcher(
            publisher, "chunking-queue"
        ).dispatch(job_id)
        await RabbitMQEmbeddingDispatcher(
            publisher, "embedding-queue"
        ).dispatch_job(job_id)
        await RabbitMQClassificationDispatcher(
            publisher, "classification-queue"
        ).dispatch_job(job_id)

        common_payload = {"ingestion_job_id": str(job_id)}
        self.assertEqual(
            publisher.calls,
            [
                (
                    "discovery-queue",
                    {
                        "ingestion_job_id": str(job_id),
                        "batch_size": 25,
                    },
                ),
                ("download-queue", common_payload),
                ("extraction-queue", common_payload),
                ("chunking-queue", common_payload),
                ("embedding-queue", common_payload),
                ("classification-queue", common_payload),
            ],
        )


if __name__ == "__main__":
    unittest.main()
