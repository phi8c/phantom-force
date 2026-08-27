from abc import ABC
from abc import abstractmethod

from module.ingest.discovery.domain.contracts.discovery_provider import (
    DiscoveryProvider,
)


class DiscoveryProviderResolver(ABC):

    @abstractmethod
    def resolve(
        self,
        *,
        provider: str,
        configuration: dict | None = None,
    ) -> DiscoveryProvider:
        pass
