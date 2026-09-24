from __future__ import annotations

from typing import Protocol

from .message import ReceivedMessage


class MessageConsumer(Protocol):
    """Polling receive boundary implemented by each messaging provider."""

    async def receive(
        self,
        *,
        max_messages: int = 1,
        wait_timeout: float = 5,
    ) -> list[ReceivedMessage]: ...
