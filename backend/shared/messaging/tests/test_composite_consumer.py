from __future__ import annotations

import asyncio
import unittest

from shared.messaging.composition import (
    CompositeConsumerError,
    CompositeMessageConsumer,
    IngestConsumers,
    MessagingResourceGroup,
    create_composite_consumers,
)


class FakeMessage:
    def __init__(self, value: str) -> None:
        self.payload = {"value": value}

    async def ack(self) -> None:
        return None

    async def nack(self, *, requeue: bool = True) -> None:
        return None


class ScriptedConsumer:
    def __init__(
        self,
        result=None,
        *,
        delay: float = 0,
        error: Exception | None = None,
    ) -> None:
        self.result = result if result is not None else []
        self.delay = delay
        self.error = error
        self.calls = 0
        self.cancelled = False

    async def receive(self, **kwargs):
        self.calls += 1
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        if self.error is not None:
            raise self.error
        return list(self.result)


def ingest_consumers(consumer) -> IngestConsumers:
    return IngestConsumers(
        discovery=consumer,
        download=consumer,
        extraction=consumer,
        chunking=consumer,
        embedding=consumer,
        classification=consumer,
    )


class CompositeMessageConsumerTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_first_message_and_buffers_simultaneous_result(self) -> None:
        rabbit_message = FakeMessage("rabbit")
        azure_message = FakeMessage("azure")
        rabbit = ScriptedConsumer([rabbit_message])
        azure = ScriptedConsumer([azure_message])
        consumer = CompositeMessageConsumer(
            {
                "rabbitmq": rabbit,
                "azure_service_bus": azure,
            }
        )

        first = await consumer.receive(max_messages=1)
        second = await consumer.receive(max_messages=1)

        self.assertEqual(
            {first[0].payload["value"], second[0].payload["value"]},
            {"rabbit", "azure"},
        )
        self.assertEqual(rabbit.calls, 1)
        self.assertEqual(azure.calls, 1)

    async def test_empty_provider_does_not_cancel_provider_with_message(self) -> None:
        message = FakeMessage("azure")
        empty = ScriptedConsumer([])
        delayed = ScriptedConsumer([message], delay=0.01)
        consumer = CompositeMessageConsumer(
            {
                "rabbitmq": empty,
                "azure_service_bus": delayed,
            }
        )

        received = await consumer.receive(max_messages=1)

        self.assertEqual(received, [message])
        self.assertFalse(delayed.cancelled)

    async def test_one_provider_failure_does_not_block_other_provider(self) -> None:
        message = FakeMessage("rabbit")
        consumer = CompositeMessageConsumer(
            {
                "azure_service_bus": ScriptedConsumer(
                    error=RuntimeError("azure unavailable")
                ),
                "rabbitmq": ScriptedConsumer([message], delay=0.01),
            }
        )

        self.assertEqual(await consumer.receive(), [message])

    async def test_all_provider_failures_raise_clear_error(self) -> None:
        consumer = CompositeMessageConsumer(
            {
                "azure_service_bus": ScriptedConsumer(
                    error=RuntimeError("azure unavailable")
                ),
                "rabbitmq": ScriptedConsumer(
                    error=RuntimeError("rabbit unavailable")
                ),
            }
        )

        with self.assertRaisesRegex(
            CompositeConsumerError,
            "All messaging providers failed",
        ):
            await consumer.receive()

    async def test_composes_all_six_stages(self) -> None:
        rabbit = ScriptedConsumer()
        azure = ScriptedConsumer()

        consumers = create_composite_consumers(
            {
                "rabbitmq": ingest_consumers(rabbit),
                "azure_service_bus": ingest_consumers(azure),
            }
        )

        for stage in (
            consumers.discovery,
            consumers.download,
            consumers.extraction,
            consumers.chunking,
            consumers.embedding,
            consumers.classification,
        ):
            self.assertIsInstance(stage, CompositeMessageConsumer)


class MessagingResourceGroupTests(unittest.IsolatedAsyncioTestCase):
    async def test_closes_all_resources_in_reverse_order(self) -> None:
        calls = []

        async def close_azure() -> None:
            calls.append("azure")

        async def close_rabbit() -> None:
            calls.append("rabbit")

        resources = MessagingResourceGroup(
            [close_azure, close_rabbit]
        )

        await resources.close()
        await resources.close()

        self.assertEqual(calls, ["rabbit", "azure"])

    async def test_continues_cleanup_after_failure(self) -> None:
        calls = []

        async def close_azure() -> None:
            calls.append("azure")

        async def close_rabbit() -> None:
            calls.append("rabbit")
            raise RuntimeError("rabbit close failed")

        resources = MessagingResourceGroup(
            [close_azure, close_rabbit]
        )

        with self.assertRaisesRegex(RuntimeError, "rabbit close failed"):
            await resources.close()

        self.assertEqual(calls, ["rabbit", "azure"])


if __name__ == "__main__":
    unittest.main()
