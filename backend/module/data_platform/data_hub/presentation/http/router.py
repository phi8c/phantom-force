from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from bootstrap.database import async_session_factory
from module.data_platform.data_hub.composition.browser_factory import (
    create_browser_provider_registry,
)
from module.data_platform.data_hub.composition.browser_registry import (
    UnsupportedBrowserProviderError,
)
from module.data_platform.data_hub.shared.application.browser_service import (
    BrowseResult,
    DataHubBrowserService,
)
from module.data_platform.data_hub.shared.domain.contracts.browser import (
    InvalidBrowseLocatorError,
)
from module.knowledge_space.application.services.data_hub_configuration_resolver import (
    DataHubConfigurationDisabledError,
    DataHubConfigurationNotFoundError,
    KnowledgeSpaceDataHubConfigurationResolver,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_data_hub_repository_impl import (
    KnowledgeSpaceDataHubRepositoryImpl,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)

from .schemas import BrowseRequest, BrowseResponse, DataHubBrowseNodeResponse


router = APIRouter(prefix="/data-hub/knowledge-spaces", tags=["Data Hub"])


async def get_browser_service() -> AsyncIterator[DataHubBrowserService]:
    async with async_session_factory() as session:
        yield DataHubBrowserService(
            KnowledgeSpaceDataHubConfigurationResolver(
                KnowledgeSpaceDataHubRepositoryImpl(session),
                DataHubProviderRepositoryImpl(session),
            ),
            create_browser_provider_registry(),
        )


@router.get("/{knowledge_space_id}/browse", response_model=BrowseResponse)
async def browse_root(
    knowledge_space_id: UUID,
    service: DataHubBrowserService = Depends(get_browser_service),
) -> BrowseResponse:
    return await _execute(service.browse_root(knowledge_space_id))


@router.post("/{knowledge_space_id}/browse", response_model=BrowseResponse)
async def browse_children(
    knowledge_space_id: UUID,
    request: BrowseRequest,
    service: DataHubBrowserService = Depends(get_browser_service),
) -> BrowseResponse:
    return await _execute(service.browse_children(knowledge_space_id, request.locator))


async def _execute(operation) -> BrowseResponse:
    try:
        result = await operation
    except DataHubConfigurationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DataHubConfigurationDisabledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnsupportedBrowserProviderError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidBrowseLocatorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Data Hub provider request failed.") from exc
    return _response(result)


def _response(result: BrowseResult) -> BrowseResponse:
    return BrowseResponse(
        provider=result.provider,
        nodes=[
            DataHubBrowseNodeResponse(
                id=node.id,
                name=node.name,
                type=node.type,
                has_children=node.has_children,
                provider=node.provider,
                locator=dict(node.locator),
            )
            for node in result.nodes
        ],
    )
