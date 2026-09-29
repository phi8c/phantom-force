from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class UnsupportedDataHubProviderError(LookupError):
    pass


ProviderFactory = Callable[[Mapping[str, Any]], object]


class DataHubProviderRegistry:
    def __init__(self, factories: Mapping[str, ProviderFactory]) -> None:
        self._factories = {
            code.strip().lower(): factory
            for code, factory in factories.items()
        }

    def resolve(
        self,
        provider: str,
        configuration: Mapping[str, Any] | None = None,
    ) -> object:
        code = provider.strip().lower()
        try:
            factory = self._factories[code]
        except KeyError as exc:
            raise UnsupportedDataHubProviderError(
                f"Unsupported Data Hub provider: {provider}"
            ) from exc
        return factory(configuration or {})
