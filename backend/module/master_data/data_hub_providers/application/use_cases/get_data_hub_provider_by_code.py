from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)
from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)


class GetDataHubProviderByCodeUseCase:

    def __init__(
        self,
        repository: DataHubProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        code: str,
    ) -> DataHubProvider | None:

        return await self.repository.get_by_code(
            code,
        )