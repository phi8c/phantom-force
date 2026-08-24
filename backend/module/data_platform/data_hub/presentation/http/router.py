from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends

from module.data_platform.data_hub.application.services.data_hub_service import (
    DataHubService,
)
from module.data_platform.data_hub.domain.entities.discovered_file import (
    DiscoveredFile,
)
from module.data_platform.data_hub.domain.value_objects.source_reference import (
    SourceReference,
)

from .dependencies import build_data_hub_service
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