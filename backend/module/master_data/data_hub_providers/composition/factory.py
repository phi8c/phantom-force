from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.master_data.data_hub_providers.application.services.data_hub_provider_service import (
    DataHubProviderService,
)
from module.master_data.data_hub_providers.application.use_cases.get_data_hub_provider import (
    GetDataHubProviderUseCase,
)
from module.master_data.data_hub_providers.application.use_cases.get_data_hub_provider_by_code import (
    GetDataHubProviderByCodeUseCase,
)
from module.master_data.data_hub_providers.application.use_cases.list_data_hub_providers import (
    ListDataHubProvidersUseCase,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)


def create_data_hub_provider_service(
    session: AsyncSession,
) -> DataHubProviderService:

    repository = DataHubProviderRepositoryImpl(
        session=session,
    )

    get_provider = GetDataHubProviderUseCase(
        repository=repository,
    )

    get_provider_by_code = (
        GetDataHubProviderByCodeUseCase(
            repository=repository,
        )
    )

    list_providers = ListDataHubProvidersUseCase(
        repository=repository,
    )

    return DataHubProviderService(
        get_provider=get_provider,
        get_provider_by_code=get_provider_by_code,
        list_providers=list_providers,
    )
