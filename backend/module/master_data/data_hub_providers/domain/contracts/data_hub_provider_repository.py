from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)


class DataHubProviderRepository(ABC):

    @abstractmethod
    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> DataHubProvider | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> DataHubProvider | None:
        pass

    @abstractmethod
    async def list_enabled(
        self,
    ) -> list[DataHubProvider]:
        pass
