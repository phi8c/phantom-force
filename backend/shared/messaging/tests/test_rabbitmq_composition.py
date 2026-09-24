from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from shared.messaging.rabbitmq.composition.factory import (
    create_rabbitmq_consumers,
    create_rabbitmq_dispatchers,
    create_rabbitmq_producer,
)


def fake_settings():
    return SimpleNamespace(
        RABBITMQ_URL="amqps://user:password@example/vhost",
        RABBITMQ_DISCOVERY_QUEUE="discovery-queue",
        RABBITMQ_DOWNLOAD_QUEUE="download-queue",
        RABBITMQ_EXTRACT_QUEUE="extraction-queue",
        RABBITMQ_CHUNK_QUEUE="chunking-queue",
        RABBITMQ_EMBED_QUEUE="embedding-queue",
        RABBITMQ_CLASSIFY_QUEUE="classification-queue",
    )


class FakeTransport:
    instances = []

    def __init__(self, url: str) -> None:
        self.url = url
        self.consumer_queues = []
        self.publisher = RecordingPublisher()
        self.closed = False
        self.__class__.instances.append(self)

    async def create_consumer(self, queue_name: str):
        self.consumer_queues.append(queue_name)
        return f"consumer:{queue_name}"

    async def create_publisher(self):
        return self.publisher

    async def close(self) -> None:
        self.closed = True


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls = []

    async def publish(self, queue_name: str, payload: dict) -> None:
        self.calls.append((queue_name, payload))


class RabbitMQCompositionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        FakeTransport.instances.clear()

    async def test_maps_url_and_all_six_queue_names(self) -> None:
        with (
            patch(
                "shared.messaging.rabbitmq.composition.factory._settings",
                return_value=fake_settings(),
            ),
            patch(
                "shared.messaging.rabbitmq.composition.factory.RabbitMQTransport",
                FakeTransport,
            ),
        ):
            resources = await create_rabbitmq_consumers()

        transport = FakeTransport.instances[0]
        self.assertEqual(transport.url, fake_settings().RABBITMQ_URL)
        self.assertEqual(
            transport.consumer_queues,
            [
                "discovery-queue",
                "download-queue",
                "extraction-queue",
                "chunking-queue",
                "embedding-queue",
                "classification-queue",
            ],
        )
        self.assertEqual(
            resources.consumers.discovery,
            "consumer:discovery-queue",
        )

    async def test_producer_creates_publisher_without_consumers(self) -> None:
        with (
            patch(
                "shared.messaging.rabbitmq.composition.factory._settings",
                return_value=fake_settings(),
            ),
            patch(
                "shared.messaging.rabbitmq.composition.factory.RabbitMQTransport",
                FakeTransport,
            ),
        ):
            resources = await create_rabbitmq_producer()

        transport = FakeTransport.instances[0]
        self.assertEqual(transport.consumer_queues, [])

        await resources.close()
        self.assertTrue(transport.closed)

    async def test_dispatchers_use_the_matching_queue_names(self) -> None:
        with (
            patch(
                "shared.messaging.rabbitmq.composition.factory._settings",
                return_value=fake_settings(),
            ),
            patch(
                "shared.messaging.rabbitmq.composition.factory.RabbitMQTransport",
                FakeTransport,
            ),
        ):
            resources = await create_rabbitmq_consumers()
            dispatchers = await create_rabbitmq_dispatchers(resources)

        job_id = uuid4()
        await dispatchers.discovery.dispatch(job_id, 20)
        await dispatchers.download.dispatch(job_id)
        await dispatchers.extraction.dispatch(job_id)
        await dispatchers.chunking.dispatch(job_id)
        await dispatchers.embedding.dispatch_job(job_id)
        await dispatchers.classification.dispatch_job(job_id)

        self.assertEqual(
            [queue for queue, _ in resources.transport.publisher.calls],
            [
                "discovery-queue",
                "download-queue",
                "extraction-queue",
                "chunking-queue",
                "embedding-queue",
                "classification-queue",
            ],
        )

    async def test_partial_consumer_failure_closes_transport(self) -> None:
        class FailingTransport(FakeTransport):
            async def create_consumer(self, queue_name: str):
                if queue_name == "extraction-queue":
                    raise RuntimeError("declaration failed")
                return await super().create_consumer(queue_name)

        with (
            patch(
                "shared.messaging.rabbitmq.composition.factory._settings",
                return_value=fake_settings(),
            ),
            patch(
                "shared.messaging.rabbitmq.composition.factory.RabbitMQTransport",
                FailingTransport,
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "declaration failed"):
                await create_rabbitmq_consumers()

        self.assertTrue(FailingTransport.instances[-1].closed)


if __name__ == "__main__":
    unittest.main()
