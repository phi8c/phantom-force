from uuid import UUID

from module.master_data.data_hub_providers.application.use_cases.get_data_hub_provider import (
    GetDataHubProviderUseCase,
)
from module.master_data.data_hub_providers.application.use_cases.get_data_hub_provider_by_code import (
    GetDataHubProviderByCodeUseCase,
)
from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)


class DataHubProviderService:

    def __init__(
        self,
        get_provider: GetDataHubProviderUseCase,
        get_provider_by_code: GetDataHubProviderByCodeUseCase,
    ):
        self._get_provider = get_provider
        self._get_provider_by_code = (
            get_provider_by_code
        )

    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> DataHubProvider | None:

        return await self._get_provider.execute(
            provider_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> DataHubProvider | None:

        return await self._get_provider_by_code.execute(
            code,
        )