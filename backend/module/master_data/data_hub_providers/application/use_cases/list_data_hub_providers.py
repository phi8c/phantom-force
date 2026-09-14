from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)
from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)


class ListDataHubProvidersUseCase:

    def __init__(
        self,
        repository: DataHubProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[DataHubProvider]:

        return await self.repository.list_enabled()
