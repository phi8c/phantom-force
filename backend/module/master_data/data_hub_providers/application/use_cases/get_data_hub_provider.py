from uuid import UUID

from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)
from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)


class GetDataHubProviderUseCase:

    def __init__(
        self,
        repository: DataHubProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider_id: UUID,
    ) -> DataHubProvider | None:

        return await self.repository.get_by_id(
            provider_id,
        )