from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from module.data_platform.data_hub.shared.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.shared.domain.value_objects.source_reference import (
    SourceReference,
)

from ...domain.entities.browse_node import DropboxBrowseNode
from ...provider import DropboxProvider
from .schemas import BrowseNodeResponse, DiscoverRequest, DiscoveredFileResponse
from .schemas import DiscoveryPageResponse


router = APIRouter(prefix="/data-hub/dropbox", tags=["Dropbox Data Hub"])


def get_dropbox_provider() -> DropboxProvider:
    raise NotImplementedError(
        "DropboxProvider dependency must be supplied by a standalone test app or composition root."
    )


@router.get("/root/children", response_model=list[BrowseNodeResponse])
async def list_root_children(
    provider: DropboxProvider = Depends(get_dropbox_provider),
) -> list[BrowseNodeResponse]:
    nodes = await provider.browser.list_root_children()
    return [_browse_response(node) for node in nodes]


@router.get("/folders/children", response_model=list[BrowseNodeResponse])
async def list_folder_children(
    path: str = Query(...),
    provider: DropboxProvider = Depends(get_dropbox_provider),
) -> list[BrowseNodeResponse]:
    nodes = await provider.browser.list_folder_children(path)
    return [_browse_response(node) for node in nodes]


@router.post("/discover", response_model=DiscoveryPageResponse)
async def discover(
    request: DiscoverRequest,
    provider: DropboxProvider = Depends(get_dropbox_provider),
) -> DiscoveryPageResponse:
    page = await provider.discovery.discover(
        SourceReference(
            provider="dropbox",
            identifier=request.identifier,
            metadata=request.metadata,
        ),
        cursor=request.cursor,
        limit=request.limit,
    )
    return DiscoveryPageResponse(
        items=[_file_response(file) for file in page.items],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


def _browse_response(node: DropboxBrowseNode) -> BrowseNodeResponse:
    return BrowseNodeResponse(
        id=node.id,
        name=node.name,
        type=node.type,
        path_lower=node.path_lower,
        path_display=node.path_display,
        parent_path=node.parent_path,
        has_children=node.has_children,
    )


def _file_response(file: DiscoveredFile) -> DiscoveredFileResponse:
    return DiscoveredFileResponse(
        external_file_id=file.external_file_id,
        file_name=file.file_name,
        file_extension=file.file_extension,
        file_size_bytes=file.file_size_bytes,
        source_file_url=file.source_file_url,
        provider_metadata=dict(file.provider_metadata),
        last_modified_at=file.last_modified_at.isoformat() if file.last_modified_at else None,
        original_file_path=file.original_file_path,
    )
