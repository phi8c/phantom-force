from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from module.data_platform.data_hub.shared.domain.contracts.file_downloader import (
    FileDownloader,
)


class UnsupportedDataHubDownloaderError(LookupError):
    pass


CloseCallback = Callable[[], Awaitable[None]]


async def _no_op_close() -> None:
    return None


@dataclass(frozen=True, slots=True)
class DataHubDownloaderResource:
    downloader: FileDownloader
    _close_callback: CloseCallback = field(
        default=_no_op_close,
        repr=False,
    )

    async def close(self) -> None:
        await self._close_callback()


DownloaderFactory = Callable[
    [Mapping[str, Any]],
    DataHubDownloaderResource,
]


class DataHubDownloaderRegistry:
    def __init__(
        self,
        factories: Mapping[str, DownloaderFactory],
    ) -> None:
        self._factories = {
            code.strip().lower(): factory
            for code, factory in factories.items()
        }

    def create(
        self,
        provider: str,
        configuration: Mapping[str, Any] | None = None,
    ) -> DataHubDownloaderResource:
        code = provider.strip().lower()
        try:
            factory = self._factories[code]
        except KeyError as exc:
            raise UnsupportedDataHubDownloaderError(
                f"Unsupported Data Hub download provider: {provider}"
            ) from exc
        return factory(configuration or {})
