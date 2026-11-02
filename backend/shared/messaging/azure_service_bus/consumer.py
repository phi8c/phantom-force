from __future__ import annotations

import json
import asyncio
import logging
from typing import Any

from shared.messaging.contracts import MessageConsumer, ReceivedMessage


class AzureReceivedMessage(ReceivedMessage):
    def __init__(self, receiver: Any, raw_message: Any, *, renew_interval: float = 10) -> None:
        self._receiver = receiver
        self._raw_message = raw_message
        self._payload: dict[str, Any] | None = None
        self._renewal_error: Exception | None = None
        if renew_interval <= 0:
            raise ValueError('Message renewal interval must be positive')
        self._renew_interval = renew_interval
        self._renewal = None
        if callable(getattr(receiver, 'renew_message_lock', None)):
            self._renewal = asyncio.create_task(self._renew_lock())

    async def _renew_lock(self):
        try:
            while True:
                await asyncio.sleep(self._renew_interval)
                await self._receiver.renew_message_lock(self._raw_message)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self._renewal_error = error
            logging.getLogger(__name__).exception('Azure message lock renewal failed')

    async def stop_renewal(self):
        if self._renewal is not None:
            self._renewal.cancel()
            await asyncio.gather(self._renewal, return_exceptions=True)

    @property
    def payload(self) -> dict[str, Any]:
        if self._payload is None:
            self._payload = self._parse_payload(self._raw_message)
        return self._payload

    async def ack(self) -> None:
        try:
            if self._renewal_error is not None:
                raise RuntimeError('Azure message lock renewal failed') from self._renewal_error
            await self._receiver.complete_message(self._raw_message)
        finally:
            await self.stop_renewal()

    async def nack(self, *, requeue: bool = True) -> None:
        try:
            if requeue:
                await self._receiver.abandon_message(self._raw_message)
                return
            await self._receiver.dead_letter_message(self._raw_message)
        finally:
            await self.stop_renewal()

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
        self._active: set[AzureReceivedMessage] = set()

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
        self._active = {message for message in self._active
                        if message._renewal is not None and not message._renewal.done()}
        received = [
            AzureReceivedMessage(self._receiver, message)
            for message in messages
        ]
        self._active.update(received)
        return received

    async def close(self) -> None:
        await asyncio.gather(*(message.stop_renewal() for message in self._active))
        self._active.clear()
        await self._receiver.close()
