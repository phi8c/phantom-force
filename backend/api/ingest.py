from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from bootstrap.modules import start_ingestion_use_case_scope
from bootstrap.queues import (
    close_ingest_queue_clients,
    create_ingest_dispatchers,
    create_ingest_queue_clients,
)
from module.ingest.config.application.dtos.start_ingestion import (
    StartIngestionCommand,
)


router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
)


class StartIngestionRequest(BaseModel):
    batch_size: int = 1000


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


async def _dispatch_discovery(
    *,
    ingestion_job_id: UUID,
    batch_size: int,
) -> None:
    queues = create_ingest_queue_clients()

    try:
        dispatchers = create_ingest_dispatchers(
            queues,
        )

        await dispatchers.discovery.dispatch(
            ingestion_job_id=ingestion_job_id,
            batch_size=batch_size,
        )

    finally:
        await close_ingest_queue_clients(
            queues,
        )


def _validate_batch_size(
    batch_size: int,
) -> None:
    if batch_size <= 0:
        raise HTTPException(
            status_code=400,
            detail="batch_size must be greater than 0",
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
    _validate_batch_size(
        request.batch_size,
    )

    await _dispatch_discovery(
        ingestion_job_id=ingestion_job_id,
        batch_size=request.batch_size,
    )

    return {
        "ingestion_job_id": str(
            ingestion_job_id
        ),
        "status": "QUEUED",
    }
