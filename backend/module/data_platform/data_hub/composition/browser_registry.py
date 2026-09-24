from __future__ import annotations

from collections.abc import Callable, Mapping

from module.data_platform.data_hub.shared.domain.contracts.browser import DataHubBrowser
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    ResolvedDataHubConfiguration,
)


class UnsupportedBrowserProviderError(LookupError):
    pass


BrowserFactory = Callable[[Mapping[str, object]], DataHubBrowser]


class DataHubBrowserProviderRegistry:
    def __init__(self, factories: Mapping[str, BrowserFactory]) -> None:
        self._factories = {
            code.strip().lower(): factory for code, factory in factories.items()
        }

    def create(
        self,
        resolved: ResolvedDataHubConfiguration,
    ) -> DataHubBrowser:
        code = resolved.provider.strip().lower()
        try:
            factory = self._factories[code]
        except KeyError as exc:
            raise UnsupportedBrowserProviderError(
                f"Unsupported Data Hub browser provider '{code}'."
            ) from exc
        return factory(resolved.configuration)
