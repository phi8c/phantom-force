from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict

from bootstrap.database import async_session_factory
from module.master_data.data_hub_providers.application.services.data_hub_provider_service import (
    DataHubProviderService,
)
from module.master_data.data_hub_providers.composition.factory import (
    create_data_hub_provider_service,
)


class DataHubProviderSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    provider: str
    configuration_schema: dict


router = APIRouter(
    prefix="/data-hub-providers",
    tags=["data-hub-providers"],
)


async def get_data_hub_provider_service() -> AsyncIterator[
    DataHubProviderService
]:
    async with async_session_factory() as session:
        yield create_data_hub_provider_service(
            session=session,
        )


@router.get(
    "",
    response_model=list[DataHubProviderSchema],
)
async def list_data_hub_providers(
    service: DataHubProviderService = Depends(
        get_data_hub_provider_service,
    ),
):
    providers = await service.list_enabled()

    return [
        {
            "id": provider.id,
            "code": provider.code,
            "name": provider.name,
            "provider": provider.provider,
            "configuration_schema": provider.configuration_schema,
        }
        for provider in providers
    ]
