from __future__ import annotations

import unittest

from shared.messaging.composition import (
    IngestConsumers,
    IngestDispatchers,
    IngestMessaging,
)


class FakeMessage:
    def __init__(self) -> None:
        self.payload = {"ingestion_job_id": "job-id"}
        self.acked = False
        self.nacked = False
        self.requeue = None

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, *, requeue: bool = True) -> None:
        self.nacked = True
        self.requeue = requeue


class FakeConsumer:
    def __init__(self, message: FakeMessage) -> None:
        self.message = message

    async def receive(
        self,
        *,
        max_messages: int = 1,
        wait_timeout: float = 5,
    ) -> list[FakeMessage]:
        return [self.message][:max_messages]


class MessagingContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_structural_message_and_consumer_contract(self) -> None:
        message = FakeMessage()
        consumer = FakeConsumer(message)

        received = await consumer.receive(max_messages=1, wait_timeout=5)
        self.assertEqual(received[0].payload, {"ingestion_job_id": "job-id"})

        await received[0].ack()
        self.assertTrue(message.acked)
        self.assertFalse(message.nacked)

        await received[0].nack(requeue=False)
        self.assertTrue(message.nacked)
        self.assertFalse(message.requeue)

    async def test_messaging_bundle_owns_provider_cleanup(self) -> None:
        message = FakeMessage()
        consumer = FakeConsumer(message)
        consumers = IngestConsumers(
            discovery=consumer,
            download=consumer,
            extraction=consumer,
            chunking=consumer,
            embedding=consumer,
            classification=consumer,
        )
        dispatcher = object()
        dispatchers = IngestDispatchers(
            discovery=dispatcher,
            download=dispatcher,
            extraction=dispatcher,
            chunking=dispatcher,
            embedding=dispatcher,
            classification=dispatcher,
        )
        closed = False

        async def close() -> None:
            nonlocal closed
            closed = True

        messaging = IngestMessaging(
            consumers=consumers,
            dispatchers=dispatchers,
            _close_callback=close,
        )

        await messaging.close()

        self.assertTrue(closed)
        self.assertIs(messaging.consumers.discovery, consumer)
        self.assertIs(messaging.dispatchers.discovery, dispatcher)


if __name__ == "__main__":
    unittest.main()
