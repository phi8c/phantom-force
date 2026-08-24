from uuid import uuid4

from fastapi import APIRouter
from fastapi import Depends
from datetime import datetime, timezone

from app.application.source.requests.create_source_request import (
    CreateSourceRequest,
)

from app.application.source.use_cases.create_source_use_case import (
    CreateSourceUseCase,
)

from app.presentation.source.schemas.source_schema import (
    CreateSourceSchema,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_source_repository,
    get_uow,
)

from app.application.source.use_cases.discover_sources_use_case import (
    DiscoverSourcesUseCase,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_sharepoint_service,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_document_source,
)
from app.domain.entities.ingestion_run import IngestionRun
from app.domain.enums.ingestion_status import IngestionStatus
from app.presentation.ingestion.dependencies.ingestion_dependencies import get_ingestion_planner
from app.presentation.ingestion.schemas.ingestion_schema import StartIngestionRequest


router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


@router.post("/")
async def create_source(
    payload: CreateSourceSchema,
    repository=Depends(
        get_source_repository,
    ),
    uow=Depends(
        get_uow,
    ),
):

    use_case = CreateSourceUseCase(
        repository,
        uow,
    )

    return await use_case.execute(
        CreateSourceRequest(
            name=payload.name,
            source_type=payload.source_type,
            site_id=payload.site_id,
            drive_id=payload.drive_id,
        )
    )
    
@router.get(
    "/discover"
)
async def discover_sources(
    sharepoint_service=Depends(
        get_sharepoint_service,
    ),
):

    use_case = (
        DiscoverSourcesUseCase(
            sharepoint_service,
        )
    )

    return await (
        use_case.execute()
    )
    
@router.post(
    "/traverse"
)
async def traverse(
    request: StartIngestionRequest,
    document_source=Depends(
    get_document_source,
)
):

    run = IngestionRun(
    id=uuid4(),

    source_id=request.source_id,

    trigger_type=request.trigger_type,

    scope_type=request.scope_type,

    scope_data={
        "site_id": request.site_id,
        "drive_id": request.drive_id,
        "folder_id": request.folder_id,
        "file_id": request.file_id,
    },

    status=IngestionStatus.PENDING,

    is_build_graph=False,

    total_files=0,

    completed_files=0,

    failed_files=0,

    started_at=None,

    finished_at=None,

    created_at=datetime.now(
        timezone.utc,
    ),
)

    files = await (
        document_source.discover_files(
            run,
        )
    )

    return {
    "count": len(files),
    "files": [
        {
            "id": file.external_file_id,
            "name": file.file_name,
            "size": file.file_size_bytes,
            "extension": file.file_extension,
            "provider_metadata": file.provider_metadata,
        }
        for file in files
    ],
}

    
    
