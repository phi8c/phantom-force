from dataclasses import asdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from bootstrap.modules import (
    create_ingestion_job_use_case_scope,
    get_ingestion_job_configuration_use_case_scope,
    get_ingestion_job_scope_use_case_scope,
    list_ingestion_jobs_use_case_scope,
    save_ingestion_job_configuration_use_case_scope,
    save_ingestion_job_scope_use_case_scope,
    start_existing_ingestion_job_use_case_scope,
    start_ingestion_use_case_scope,
)
from bootstrap.queues import (
    close_ingest_queue_clients,
    create_ingest_dispatchers,
    create_ingest_queue_clients,
)
from module.ingest.config.application.dtos.start_ingestion import (
    StartIngestionCommand,
)
from module.ingest.config.application.dtos.start_existing_ingestion_job import (
    StartExistingIngestionJobCommand,
)
from module.ingest.config.application.dtos.create_ingestion_job import (
    CreateIngestionJobCommand,
)
from module.ingest.config.application.dtos.list_ingestion_jobs import (
    ListIngestionJobsQuery,
)
from module.ingest.config.application.dtos.save_ingestion_job_configuration import (
    SaveIngestionJobConfigurationCommand,
)
from module.ingest.config.application.dtos.ingestion_job_scope import (
    SaveIngestionJobScopeCommand,
)


router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
)


class StartIngestionRequest(BaseModel):
    batch_size: int = 1000


class CreateIngestionJobRequest(BaseModel):
    knowledge_space_id: UUID
    trigger_type: str = "MANUAL"
    is_build_graph: bool = False


class SaveIngestionJobConfigurationRequest(BaseModel):
    extraction_engine_code: str
    chunking_strategy_code: str
    model_set_code: str | None = None
    is_classification: bool = False
    configuration: dict[str, Any] | None = None


class SaveIngestionJobScopeRequest(BaseModel):
    scope_type: str
    scope_data: dict[str, Any]


class CreateIngestionRequest(BaseModel):
    knowledge_space_id: UUID
    extraction_engine_code: str
    chunking_strategy_code: str
    model_set_code: str | None = None
    is_classification: bool = False
    trigger_type: str = "MANUAL"
    scope_type: str | None = "FULL"
    scope_data: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    is_build_graph: bool = False
    batch_size: int = 1000


@router.get(
    "/jobs",
)
async def list_ingestion_jobs(
    knowledge_space_id: UUID | None = None,
    status: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
):
    try:
        async with list_ingestion_jobs_use_case_scope() as use_case:
            result = await use_case.execute(
                ListIngestionJobsQuery(
                    knowledge_space_id=knowledge_space_id,
                    status=status,
                    limit=limit,
                    cursor=cursor,
                )
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(result),
    )


@router.post(
    "/jobs",
    status_code=201,
)
async def create_ingestion_job(
    request: CreateIngestionJobRequest,
):
    try:
        async with create_ingestion_job_use_case_scope() as use_case:
            result = await use_case.execute(
                CreateIngestionJobCommand(
                    knowledge_space_id=(
                        request.knowledge_space_id
                    ),
                    trigger_type=request.trigger_type,
                    is_build_graph=request.is_build_graph,
                )
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return {
        "ingestion_job_id": str(
            result.ingestion_job_id
        ),
    }


@router.get(
    "/jobs/{ingestion_job_id}/configuration",
)
async def get_ingestion_job_configuration(
    ingestion_job_id: UUID,
):
    try:
        async with (
            get_ingestion_job_configuration_use_case_scope()
        ) as use_case:
            result = await use_case.execute(
                ingestion_job_id,
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(result),
    )


@router.put(
    "/jobs/{ingestion_job_id}/configuration",
)
async def save_ingestion_job_configuration(
    ingestion_job_id: UUID,
    request: SaveIngestionJobConfigurationRequest,
):
    try:
        async with (
            save_ingestion_job_configuration_use_case_scope()
        ) as use_case:
            result = await use_case.execute(
                SaveIngestionJobConfigurationCommand(
                    ingestion_job_id=ingestion_job_id,
                    extraction_engine_code=(
                        request.extraction_engine_code
                    ),
                    chunking_strategy_code=(
                        request.chunking_strategy_code
                    ),
                    model_set_code=request.model_set_code,
                    is_classification=(
                        request.is_classification
                    ),
                    configuration=request.configuration,
                )
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(result),
    )


@router.get(
    "/jobs/{ingestion_job_id}/scope",
)
async def get_ingestion_job_scope(
    ingestion_job_id: UUID,
):
    try:
        async with (
            get_ingestion_job_scope_use_case_scope()
        ) as use_case:
            result = await use_case.execute(
                ingestion_job_id,
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(result),
    )


@router.put(
    "/jobs/{ingestion_job_id}/scope",
)
async def save_ingestion_job_scope(
    ingestion_job_id: UUID,
    request: SaveIngestionJobScopeRequest,
):
    try:
        async with (
            save_ingestion_job_scope_use_case_scope()
        ) as use_case:
            result = await use_case.execute(
                SaveIngestionJobScopeCommand(
                    ingestion_job_id=ingestion_job_id,
                    scope_type=request.scope_type,
                    scope_data=request.scope_data,
                )
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(result),
    )


@router.post(
    "/start",
)
async def create_and_start_ingestion(
    request: CreateIngestionRequest,
):
    queues = create_ingest_queue_clients()

    try:
        dispatchers = create_ingest_dispatchers(
            queues,
        )

        async with start_ingestion_use_case_scope(
            discovery_dispatcher=(
                dispatchers.discovery
            ),
        ) as use_case:
            result = await use_case.execute(
                StartIngestionCommand(
                    knowledge_space_id=(
                        request.knowledge_space_id
                    ),
                    extraction_engine_code=(
                        request.extraction_engine_code
                    ),
                    chunking_strategy_code=(
                        request.chunking_strategy_code
                    ),
                    model_set_code=request.model_set_code,
                    is_classification=(
                        request.is_classification
                    ),
                    trigger_type=request.trigger_type,
                    scope_type=request.scope_type,
                    scope_data=request.scope_data,
                    configuration=request.configuration,
                    is_build_graph=request.is_build_graph,
                    batch_size=request.batch_size,
                )
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:
        await close_ingest_queue_clients(
            queues,
        )

    return {
        "ingestion_job_id": str(
            result.ingestion_job_id
        ),
        "status": result.status,
    }


@router.post(
    "/jobs/{ingestion_job_id}/start",
)
async def start_existing_ingestion(
    ingestion_job_id: UUID,
    request: StartIngestionRequest,
):
    queues = create_ingest_queue_clients()

    try:
        dispatchers = create_ingest_dispatchers(
            queues,
        )

        async with (
            start_existing_ingestion_job_use_case_scope(
                discovery_dispatcher=(
                    dispatchers.discovery
                ),
            )
        ) as use_case:
            result = await use_case.execute(
                StartExistingIngestionJobCommand(
                    ingestion_job_id=ingestion_job_id,
                    batch_size=request.batch_size,
                )
            )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    finally:
        await close_ingest_queue_clients(
            queues,
        )

    return {
        "ingestion_job_id": str(
            result.ingestion_job_id
        ),
        "status": result.status,
    }
