from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence


CloseCallback = Callable[[], Awaitable[None]]


class MessagingResourceGroup:
    def __init__(self, close_callbacks: Sequence[CloseCallback]) -> None:
        self._close_callbacks = tuple(close_callbacks)
        self._closed = False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        first_error: BaseException | None = None
        for close in reversed(self._close_callbacks):
            try:
                await close()
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error
