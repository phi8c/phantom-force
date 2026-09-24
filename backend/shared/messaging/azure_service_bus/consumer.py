from __future__ import annotations

import json
from typing import Any

from shared.messaging.contracts import MessageConsumer, ReceivedMessage


class AzureReceivedMessage(ReceivedMessage):
    def __init__(self, receiver: Any, raw_message: Any) -> None:
        self._receiver = receiver
        self._raw_message = raw_message
        self._payload: dict[str, Any] | None = None

    @property
    def payload(self) -> dict[str, Any]:
        if self._payload is None:
            self._payload = self._parse_payload(self._raw_message)
        return self._payload

    async def ack(self) -> None:
        await self._receiver.complete_message(self._raw_message)

    async def nack(self, *, requeue: bool = True) -> None:
        if requeue:
            await self._receiver.abandon_message(self._raw_message)
            return
        await self._receiver.dead_letter_message(self._raw_message)

    @staticmethod
    def _parse_payload(raw_message: Any) -> dict[str, Any]:
        try:
            payload = json.loads(str(raw_message))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Azure Service Bus message contains invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Azure Service Bus message payload must be a JSON object.")
        return payload


class AzureMessageConsumer(MessageConsumer):
    def __init__(self, receiver: Any) -> None:
        self._receiver = receiver

    async def receive(
        self,
        *,
        max_messages: int = 1,
        wait_timeout: float = 5,
    ) -> list[ReceivedMessage]:
        messages = await self._receiver.receive_messages(
            max_message_count=max_messages,
            max_wait_time=wait_timeout,
        )
        return [
            AzureReceivedMessage(self._receiver, message)
            for message in messages
        ]

    async def close(self) -> None:
        await self._receiver.close()
