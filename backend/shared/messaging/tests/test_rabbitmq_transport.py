from __future__ import annotations

import unittest

from shared.messaging.rabbitmq.consumer import RabbitMQMessageConsumer
from shared.messaging.rabbitmq.transport import RabbitMQTransport


class FakeIncomingMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.acked = False
        self.nack_requeue = None

    async def ack(self) -> None:
        self.acked = True

    async def nack(self, *, requeue: bool = True) -> None:
        self.nack_requeue = requeue


class FakeQueue:
    def __init__(self, messages: list[FakeIncomingMessage | None]) -> None:
        self.messages = messages
        self.get_calls = []

    async def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return self.messages.pop(0) if self.messages else None


class FakeChannel:
    def __init__(self, queue: FakeQueue) -> None:
        self.queue = queue
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
        consumer = RabbitMQMessageConsumer(FakeQueue([first, second]))

        messages = await consumer.receive(max_messages=2, wait_timeout=1)
        await messages[0].ack()
        await messages[1].nack(requeue=True)

        self.assertEqual(messages[0].payload["ingestion_job_id"], "job-1")
        self.assertTrue(first.acked)
        self.assertTrue(second.nack_requeue)

    async def test_invalid_json_is_not_acknowledged(self) -> None:
        raw = FakeIncomingMessage(b"not-json")
        message = (
            await RabbitMQMessageConsumer(FakeQueue([raw])).receive(
                wait_timeout=1
            )
        )[0]

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            _ = message.payload

        self.assertFalse(raw.acked)
        self.assertIsNone(raw.nack_requeue)

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

    async def test_receive_uses_manual_ack_mode(self) -> None:
        raw = FakeIncomingMessage(b'{"ingestion_job_id":"job"}')
        queue = FakeQueue([raw])
        consumer = RabbitMQMessageConsumer(queue)

        await consumer.receive(max_messages=1, wait_timeout=1)

        self.assertEqual(queue.get_calls[0]["no_ack"], False)
        self.assertEqual(queue.get_calls[0]["fail"], False)


if __name__ == "__main__":
    unittest.main()
