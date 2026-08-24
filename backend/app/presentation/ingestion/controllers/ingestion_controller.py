import os
from unittest import result

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.application.ingestion.use_cases.start_ingestion_use_case import (
    StartIngestionUseCase,
)

from app.presentation.ingestion.dependencies.ingestion_dependencies import (
    get_document_extractor,
    get_ingestion_planner,
    get_ingestion_run_repository,
    get_uow,
)

from app.presentation.ingestion.schemas.ingestion_schema import (
    StartIngestionRequest,
)

from app.domain.entities.ingestion_run import (
    IngestionRun,
)

from app.domain.enums.ingestion_status import (
    IngestionStatus,
)

from app.presentation.ingestion.dependencies.ingestion_dependencies import (
    get_document_repository,
)

from app.presentation.source.dependencies.source_dependencies import (
    get_sharepoint_service,
)
from app.presentation.ingestion.dependencies.ingestion_dependencies import (
    get_document_source,
)

from app.presentation.ingestion.dependencies.ingestion_dependencies import (
    get_download_dispatcher,
)

from uuid import uuid4

from datetime import datetime
from datetime import timezone

from app.application.ingestion.requests.download_file_request import DownloadFileRequest

router = APIRouter(
    prefix="/ingestions",
    tags=["Ingestions"],
)


@router.post("/")
async def start_ingestion(
    request: StartIngestionRequest,
    repository=Depends(
        get_ingestion_run_repository,
    ),
    document_repository=Depends(
        get_document_repository,
    ),
    document_source=Depends(
        get_document_source,
    ),
    download_dispatcher=Depends(
        get_download_dispatcher,
    ),
    uow=Depends(
        get_uow,
    ),
):

    use_case = (
        StartIngestionUseCase(
            repository=repository,
            document_repository=(
                document_repository
            ),
            document_source=(
                document_source
            ),
            download_dispatcher=(
                download_dispatcher
            ),
            uow=uow,
        )
    )

    result = await (
        use_case.execute(
            source_id=(
                request.source_id
            ),
            trigger_type=(
                request.trigger_type
            ),
            scope_type=(
                request.scope_type
            ),
            is_build_graph=(
                request.configuration.graph.enabled
            ),
            configuration=(
                request.configuration
            ),
            site_id=(
                request.site_id
            ),
            drive_id=(
                request.drive_id
            ),
            folder_id=(
                request.folder_id
            ),
            file_id=(
                request.file_id
            ),
        )
    )

    return {
        "ingestion_run_id": str(
            result.id
        ),
        "status": result.status,
        "total_files": (
            result.total_files
        ),
    }
@router.post(
    "/traverse"
)
async def traverse(
    request: StartIngestionRequest,
    planner=Depends(
        get_ingestion_planner,
    ),
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
        configuration=request.configuration,
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
        planner.discover_files(
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

@router.post(
    "/test-download"
)
async def test_download(
    request: DownloadFileRequest,
    sharepoint_service=Depends(
        get_sharepoint_service,
    ),
):

    content = await (
    sharepoint_service.download_file(
        drive_id=request.drive_id,
        file_id=request.file_id,
    )
)

    file_name = (
        request.file_id
        + ".docx"
    )

    os.makedirs(
        "temp",
        exist_ok=True,
    )

    file_path = (
        f"temp/{file_name}"
    )

    with open(
        file_path,
        "wb",
    ) as file:
        file.write(
            content,
        )

    return {
        "success": True,
        "downloaded_bytes": len(content),
        "file_path": file_path,
    }
@router.post(
    "/test-extract"
)
async def test_extract(
    document_id: str,
    document_repository=Depends(
        get_document_repository,
    ),
    document_extractor=Depends(
        get_document_extractor,
    ),
):

    document = await (
        document_repository.get_by_id(
            document_id,
        )
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if not document.temp_file_path:
        raise HTTPException(
            status_code=400,
            detail="Document has no temp file",
        )

    result = await (
        document_extractor.extract(
            document.temp_file_path,
        )
    )
    
    print("in ra type result", type(result))

    return result.model_dump()