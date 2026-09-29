from __future__ import annotations

import asyncio
import unittest

from shared.messaging.rabbitmq.consumer import RabbitMQMessageConsumer
from shared.messaging.rabbitmq.transport import RabbitMQTransport


class FakeIncomingMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.ack_count = 0
        self.nack_calls = []

    async def ack(self) -> None:
        self.ack_count += 1

    async def nack(self, *, requeue: bool = True) -> None:
        self.nack_calls.append(requeue)


class FakeQueue:
    def __init__(self, messages: list[FakeIncomingMessage] | None = None) -> None:
        self.messages = messages
        self.consume_calls = []
        self.cancel_calls = []
        self.callback = None
        self.channel = None

    async def consume(self, callback, *, no_ack: bool):
        self.consume_calls.append({"no_ack": no_ack})
        self.callback = callback
        for message in self.messages or []:
            await callback(message)
        self.messages = []
        return "consumer-tag"

    async def cancel(self, consumer_tag: str) -> None:
        self.cancel_calls.append(consumer_tag)

    async def push(self, message: FakeIncomingMessage) -> None:
        if self.callback is None:
            raise AssertionError("Consumer has not been registered")
        await self.callback(message)

    async def get(self, **kwargs):
        raise AssertionError("Basic.Get must not be used")


class FakeChannel:
    def __init__(self, queue: FakeQueue) -> None:
        self.queue = queue
        self.queue.channel = self
        self.qos = None
        self.declaration = None
        self.is_closed = False

    async def set_qos(self, **kwargs) -> None:
        self.qos = kwargs

    async def declare_queue(self, queue_name: str, **kwargs):
        self.declaration = (queue_name, kwargs)
        return self.queue

    async def close(self) -> None:
        self.is_closed = True


class FakeConnection:
    def __init__(self, channels: list[FakeChannel]) -> None:
        self.channels = channels
        self.is_closed = False
        self.channel_calls = 0

    async def channel(self):
        channel = self.channels[self.channel_calls]
        self.channel_calls += 1
        return channel

    async def close(self) -> None:
        self.is_closed = True


class RabbitMQTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_message_parses_json_and_maps_ack_nack(self) -> None:
        first = FakeIncomingMessage(b'{"ingestion_job_id":"job-1"}')
        second = FakeIncomingMessage(b'{"ingestion_job_id":"job-2"}')
        third = FakeIncomingMessage(b'{"ingestion_job_id":"job-3"}')
        consumer = RabbitMQMessageConsumer(FakeQueue([first, second, third]))

        messages = await consumer.receive(max_messages=3, wait_timeout=1)
        await messages[0].ack()
        await messages[1].nack(requeue=True)
        await messages[2].nack(requeue=False)

        self.assertEqual(messages[0].payload["ingestion_job_id"], "job-1")
        self.assertEqual(first.ack_count, 1)
        self.assertEqual(second.nack_calls, [True])
        self.assertEqual(third.nack_calls, [False])

    async def test_invalid_json_is_not_acknowledged(self) -> None:
        raw = FakeIncomingMessage(b"not-json")
        message = (
            await RabbitMQMessageConsumer(FakeQueue([raw])).receive(
                wait_timeout=1
            )
        )[0]

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            _ = message.payload

        self.assertEqual(raw.ack_count, 0)
        self.assertEqual(raw.nack_calls, [])

    async def test_empty_receive_times_out_without_basic_get_or_cancel(self) -> None:
        queue = FakeQueue()
        consumer = RabbitMQMessageConsumer(queue)

        self.assertEqual(
            await consumer.receive(wait_timeout=0.001),
            [],
        )
        self.assertEqual(queue.consume_calls, [{"no_ack": False}])
        self.assertEqual(queue.cancel_calls, [])

    async def test_callback_pushes_message_to_receive(self) -> None:
        queue = FakeQueue()
        consumer = RabbitMQMessageConsumer(queue)
        await consumer.start()
        raw = FakeIncomingMessage(b'{"ingestion_job_id":"job"}')

        await queue.push(raw)
        messages = await consumer.receive(wait_timeout=0.01)

        self.assertEqual(messages[0].payload["ingestion_job_id"], "job")

    async def test_max_messages_preserves_remaining_messages(self) -> None:
        raw_messages = [
            FakeIncomingMessage(
                f'{{"ingestion_job_id":"job-{index}"}}'.encode()
            )
            for index in range(3)
        ]
        consumer = RabbitMQMessageConsumer(FakeQueue(raw_messages))

        first = await consumer.receive(max_messages=2, wait_timeout=0.01)
        second = await consumer.receive(max_messages=2, wait_timeout=0.001)

        self.assertEqual(len(first), 2)
        self.assertEqual(len(second), 1)

    async def test_repeated_empty_receive_registers_once(self) -> None:
        queue = FakeQueue()
        consumer = RabbitMQMessageConsumer(queue)

        await consumer.receive(wait_timeout=0.001)
        await consumer.receive(wait_timeout=0.001)

        self.assertEqual(queue.consume_calls, [{"no_ack": False}])

    async def test_concurrent_receive_registers_once(self) -> None:
        queue = FakeQueue()
        consumer = RabbitMQMessageConsumer(queue)

        await asyncio.gather(
            consumer.receive(wait_timeout=0.001),
            consumer.receive(wait_timeout=0.001),
        )

        self.assertEqual(queue.consume_calls, [{"no_ack": False}])

    async def test_close_cancels_registered_consumer_once(self) -> None:
        queue = FakeQueue()
        consumer = RabbitMQMessageConsumer(queue)
        await consumer.start()

        await consumer.close()
        await consumer.close()

        self.assertEqual(queue.cancel_calls, ["consumer-tag"])

    async def test_transport_reuses_connection_and_declares_durable_queues(self) -> None:
        channels = [
            FakeChannel(FakeQueue([])),
            FakeChannel(FakeQueue([])),
        ]
        connection = FakeConnection(channels)
        connect_calls = []

        async def connect(url: str, **kwargs):
            connect_calls.append((url, kwargs))
            return connection

        transport = RabbitMQTransport(
            "amqps://user:password@example/vhost",
            connect=connect,
        )
        first = await transport.create_consumer("discovery-queue")
        second = await transport.create_consumer("download-queue")

        self.assertIsInstance(first, RabbitMQMessageConsumer)
        self.assertIsInstance(second, RabbitMQMessageConsumer)
        self.assertEqual(len(connect_calls), 1)
        self.assertEqual(channels[0].qos, {"prefetch_count": 1})
        self.assertEqual(
            channels[0].declaration,
            (
                "discovery-queue",
                {
                    "durable": True,
                    "auto_delete": False,
                    "exclusive": False,
                },
            ),
        )

        await transport.close()

        self.assertTrue(all(channel.is_closed for channel in channels))
        self.assertTrue(connection.is_closed)
        self.assertEqual(
            channels[0].queue.cancel_calls,
            ["consumer-tag"],
        )
        self.assertEqual(
            channels[1].queue.cancel_calls,
            ["consumer-tag"],
        )

    async def test_consume_uses_manual_ack_mode(self) -> None:
        raw = FakeIncomingMessage(b'{"ingestion_job_id":"job"}')
        queue = FakeQueue([raw])
        consumer = RabbitMQMessageConsumer(queue)

        await consumer.receive(max_messages=1, wait_timeout=1)

        self.assertEqual(queue.consume_calls, [{"no_ack": False}])


if __name__ == "__main__":
    unittest.main()
