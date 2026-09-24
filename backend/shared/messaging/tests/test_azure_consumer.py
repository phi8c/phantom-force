from __future__ import annotations

import unittest

from shared.messaging.azure_service_bus.consumer import AzureMessageConsumer


class RawMessage:
    def __init__(self, body: str) -> None:
        self.body = body

    def __str__(self) -> str:
        return self.body


class FakeAzureReceiver:
    def __init__(self, messages: list[RawMessage]) -> None:
        self.messages = messages
        self.receive_arguments = None
        self.completed: list[RawMessage] = []
        self.abandoned: list[RawMessage] = []
        self.dead_lettered: list[RawMessage] = []
        self.closed = False

    async def receive_messages(self, **kwargs):
        self.receive_arguments = kwargs
        return self.messages

    async def complete_message(self, message: RawMessage) -> None:
        self.completed.append(message)

    async def abandon_message(self, message: RawMessage) -> None:
        self.abandoned.append(message)

    async def dead_letter_message(self, message: RawMessage) -> None:
        self.dead_lettered.append(message)

    async def close(self) -> None:
        self.closed = True


class AzureMessageConsumerTests(unittest.IsolatedAsyncioTestCase):
    async def test_receive_normalizes_payload_and_maps_arguments(self) -> None:
        raw = RawMessage('{"ingestion_job_id": "job", "batch_size": 25}')
        receiver = FakeAzureReceiver([raw])
        consumer = AzureMessageConsumer(receiver)

        messages = await consumer.receive(max_messages=2, wait_timeout=3.5)

        self.assertEqual(
            receiver.receive_arguments,
            {"max_message_count": 2, "max_wait_time": 3.5},
        )
        self.assertEqual(
            messages[0].payload,
            {"ingestion_job_id": "job", "batch_size": 25},
        )

    async def test_ack_completes_raw_message(self) -> None:
        raw = RawMessage('{"ingestion_job_id": "job"}')
        receiver = FakeAzureReceiver([raw])
        message = (await AzureMessageConsumer(receiver).receive())[0]

        await message.ack()

        self.assertEqual(receiver.completed, [raw])

    async def test_nack_maps_to_abandon_or_dead_letter(self) -> None:
        first = RawMessage('{"ingestion_job_id": "first"}')
        second = RawMessage('{"ingestion_job_id": "second"}')
        receiver = FakeAzureReceiver([first, second])
        messages = await AzureMessageConsumer(receiver).receive(max_messages=2)

        await messages[0].nack(requeue=True)
        await messages[1].nack(requeue=False)

        self.assertEqual(receiver.abandoned, [first])
        self.assertEqual(receiver.dead_lettered, [second])

    async def test_invalid_json_is_not_acknowledged(self) -> None:
        raw = RawMessage("not-json")
        receiver = FakeAzureReceiver([raw])
        message = (await AzureMessageConsumer(receiver).receive())[0]

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            _ = message.payload

        self.assertEqual(receiver.completed, [])

    async def test_close_closes_wrapped_receiver(self) -> None:
        receiver = FakeAzureReceiver([])
        consumer = AzureMessageConsumer(receiver)

        await consumer.close()

        self.assertTrue(receiver.closed)


if __name__ == "__main__":
    unittest.main()
