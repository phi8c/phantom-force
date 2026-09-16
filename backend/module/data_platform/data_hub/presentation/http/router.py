from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from module.data_platform.data_hub.application.services.data_hub_service import (
    DataHubService,
)
from module.data_platform.data_hub.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.domain.entities.browse_node import (
    BrowseNode,
)
from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)

from .schemas import BrowseNodeResponse
from .schemas import DiscoveredFileResponse
from .schemas import SourceReferenceRequest


router = APIRouter(
    prefix="/data-hub",
    tags=["Data Hub"],
)


def get_data_hub_service() -> DataHubService:
    raise NotImplementedError(
        "DataHubService dependency must be provided by the application composition root."
    )


@router.post(
    "/discover",
    response_model=list[DiscoveredFileResponse],
)
async def discover_files(
    request: SourceReferenceRequest,
    service: DataHubService = Depends(get_data_hub_service),
) -> list[DiscoveredFileResponse]:
    source = SourceReference(
        provider=request.provider,
        identifier=request.identifier,
        metadata=request.metadata,
    )

    files: list[DiscoveredFileResponse] = []

    async for discovered_file in service.discover_files(source):
        files.append(
            _to_response(discovered_file),
        )

    return files


@router.get(
    "/sharepoint/sites",
    response_model=list[BrowseNodeResponse],
)
async def list_sharepoint_sites(
    service: DataHubService = Depends(get_data_hub_service),
) -> list[BrowseNodeResponse]:
    nodes = await service.list_sharepoint_sites()
    return [_to_browse_node_response(node) for node in nodes]


@router.get(
    "/sharepoint/sites/{site_id}/drives",
    response_model=list[BrowseNodeResponse],
)
async def list_sharepoint_drives(
    site_id: str,
    service: DataHubService = Depends(get_data_hub_service),
) -> list[BrowseNodeResponse]:
    nodes = await service.list_sharepoint_drives(
        site_id=site_id,
    )
    return [_to_browse_node_response(node) for node in nodes]


@router.get(
    "/sharepoint/sites/{site_id}/drives/{drive_id}/children",
    response_model=list[BrowseNodeResponse],
)
async def list_sharepoint_drive_children(
    site_id: str,
    drive_id: str,
    service: DataHubService = Depends(get_data_hub_service),
) -> list[BrowseNodeResponse]:
    nodes = await service.list_sharepoint_drive_children(
        site_id=site_id,
        drive_id=drive_id,
    )
    return [_to_browse_node_response(node) for node in nodes]


@router.get(
    "/sharepoint/sites/{site_id}/drives/{drive_id}/items/{folder_id}/children",
    response_model=list[BrowseNodeResponse],
)
async def list_sharepoint_folder_children(
    site_id: str,
    drive_id: str,
    folder_id: str,
    service: DataHubService = Depends(get_data_hub_service),
) -> list[BrowseNodeResponse]:
    nodes = await service.list_sharepoint_folder_children(
        site_id=site_id,
        drive_id=drive_id,
        folder_id=folder_id,
    )
    return [_to_browse_node_response(node) for node in nodes]


def _to_browse_node_response(
    node: BrowseNode,
) -> BrowseNodeResponse:
    return BrowseNodeResponse(
        id=node.id,
        name=node.name,
        type=node.type,
        site_id=node.site_id,
        drive_id=node.drive_id,
        parent_id=node.parent_id,
        has_children=node.has_children,
    )


def _to_response(
    file: DiscoveredFile,
) -> DiscoveredFileResponse:
    return DiscoveredFileResponse(
        external_file_id=file.external_file_id,
        file_name=file.file_name,
        file_extension=file.file_extension,
        file_size_bytes=file.file_size_bytes,
        source_file_url=file.source_file_url,
        provider_metadata=dict(file.provider_metadata),
        last_modified_at=(
            file.last_modified_at.isoformat()
            if file.last_modified_at
            else None
        ),
        original_file_path=file.original_file_path,
    )
