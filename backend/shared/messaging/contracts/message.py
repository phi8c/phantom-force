from __future__ import annotations

from typing import Any, Protocol


class ReceivedMessage(Protocol):
    """Provider-neutral message delivered to a worker."""

    @property
    def payload(self) -> dict[str, Any]: ...

    async def ack(self) -> None: ...

    async def nack(self, *, requeue: bool = True) -> None: ...
