from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)
from module.master_data.data_hub_providers.domain.entities.data_hub_provider import (
    DataHubProvider,
)
from module.master_data.data_hub_providers.infrastructure.persistence.mappers.data_hub_provider_mapper import (
    DataHubProviderMapper,
)
from module.master_data.data_hub_providers.infrastructure.persistence.models.data_hub_provider_model import (
    DataHubProviderModel,
)


class DataHubProviderRepositoryImpl(
    DataHubProviderRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> DataHubProvider | None:

        result = await self.session.execute(
            select(
                DataHubProviderModel,
            ).where(
                DataHubProviderModel.id
                == provider_id,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return DataHubProviderMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> DataHubProvider | None:

        result = await self.session.execute(
            select(
                DataHubProviderModel,
            ).where(
                DataHubProviderModel.code
                == code,
            )
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return DataHubProviderMapper.to_entity(
            model,
        )