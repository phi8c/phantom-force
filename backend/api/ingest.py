from typing import Any
from uuid import UUID

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import bindparam
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB

from bootstrap.database import async_session_factory
from bootstrap.queues import (
    close_ingest_queue_clients,
    create_ingest_dispatchers,
    create_ingest_queue_clients,
)
from integration.ingest.configuration import (
    IngestionMasterConfigResolver,
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


async def _assert_knowledge_space_exists(
    session,
    knowledge_space_id: UUID,
) -> None:
    result = await session.execute(
        text(
            """
            SELECT id
            FROM knowledge_spaces
            WHERE id = :knowledge_space_id
            LIMIT 1
            """
        ),
        {
            "knowledge_space_id": knowledge_space_id,
        },
    )

    if result.mappings().one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="knowledge_space_id was not found",
        )


async def _create_ingestion_job(
    session,
    request: CreateIngestionRequest,
) -> UUID:
    await _assert_knowledge_space_exists(
        session,
        request.knowledge_space_id,
    )

    try:
        master_config = (
            await IngestionMasterConfigResolver(
                session,
            ).resolve(
                extraction_engine_code=(
                    request.extraction_engine_code
                ),
                chunking_strategy_code=(
                    request.chunking_strategy_code
                ),
                model_set_code=request.model_set_code,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    job_statement = text(
        """
        INSERT INTO ingestion_jobs (
            knowledge_space_id,
            trigger_type,
            status,
            is_build_graph,
            scope_type,
            scope_data
        )
        VALUES (
            :knowledge_space_id,
            :trigger_type,
            :status,
            :is_build_graph,
            :scope_type,
            :scope_data
        )
        RETURNING id
        """
    ).bindparams(
        bindparam(
            "scope_data",
            type_=JSONB,
        )
    )

    job_result = await session.execute(
        job_statement,
        {
            "knowledge_space_id": (
                request.knowledge_space_id
            ),
            "trigger_type": request.trigger_type,
            "status": "READY",
            "is_build_graph": request.is_build_graph,
            "scope_type": request.scope_type,
            "scope_data": request.scope_data or {},
        },
    )

    ingestion_job_id = (
        job_result.mappings().one()["id"]
    )

    configuration_statement = text(
        """
        INSERT INTO ingestion_job_configurations (
            ingestion_job_id,
            is_classification,
            model_set_id,
            chunking_strategy_id,
            extraction_engine_id,
            configuration
        )
        VALUES (
            :ingestion_job_id,
            :is_classification,
            :model_set_id,
            :chunking_strategy_id,
            :extraction_engine_id,
            :configuration
        )
        """
    ).bindparams(
        bindparam(
            "configuration",
            type_=JSONB,
        )
    )

    await session.execute(
        configuration_statement,
        {
            "ingestion_job_id": ingestion_job_id,
            "is_classification": (
                request.is_classification
            ),
            "model_set_id": master_config.model_set_id,
            "chunking_strategy_id": (
                master_config.chunking_strategy_id
            ),
            "extraction_engine_id": (
                master_config.extraction_engine_id
            ),
            "configuration": request.configuration or {},
        },
    )

    return ingestion_job_id


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
    _validate_batch_size(
        request.batch_size,
    )

    async with async_session_factory() as session:
        try:
            ingestion_job_id = await _create_ingestion_job(
                session,
                request,
            )

            await session.commit()

        except HTTPException:
            await session.rollback()
            raise

        except Exception as exc:
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc

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
