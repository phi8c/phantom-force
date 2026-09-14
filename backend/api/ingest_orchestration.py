import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from starlette.responses import StreamingResponse

from bootstrap.database import async_session_factory
from module.ingest.orchestration.composition import (
    create_orchestration_query_service,
)
from module.ingest.orchestration.infrastructure.persistence.queries import (
    OrchestrationQueryService,
)


router = APIRouter(
    prefix="/ingest/orchestration",
    tags=["ingest-orchestration"],
)


async def get_query_service() -> AsyncIterator[
    OrchestrationQueryService
]:
    async with async_session_factory() as session:
        yield create_orchestration_query_service(
            session=session,
        )


def _stage_counts_payload(stage_counts):
    stages: dict[str, dict[str, int]] = {}

    for count in stage_counts:
        stage_key = count.stage.lower()
        status_key = count.status.lower()

        stages.setdefault(
            stage_key,
            {},
        )[status_key] = count.count

    return stages


@router.get(
    "/jobs/{job_id}",
)
async def get_job_snapshot(
    job_id: UUID,
    query_service: OrchestrationQueryService = Depends(
        get_query_service,
    ),
):
    batches = await query_service.list_batches(
        ingestion_job_id=job_id,
    )
    stage_counts = await query_service.count_stages(
        ingestion_job_id=job_id,
    )

    batch_payloads = []

    for batch in batches:
        batch_stage_counts = (
            await query_service.list_batch_stage_counts(
                ingestion_batch_id=batch.id,
            )
        )
        batch_payloads.append(
            {
                **jsonable_encoder(asdict(batch)),
                "stages": _stage_counts_payload(
                    batch_stage_counts,
                ),
            }
        )

    return {
        "job": {
            "id": str(job_id),
            "total_batches": len(batches),
            "total_files": sum(
                batch.total_files
                for batch in batches
            ),
            "completed_files": sum(
                batch.completed_files
                for batch in batches
            ),
            "failed_files": sum(
                batch.failed_files
                for batch in batches
            ),
            "processing_batches": sum(
                1
                for batch in batches
                if batch.status == "PROCESSING"
            ),
            "completed_batches": sum(
                1
                for batch in batches
                if batch.status == "COMPLETED"
            ),
            "failed_batches": sum(
                1
                for batch in batches
                if batch.status
                in {
                    "COMPLETED_WITH_ERRORS",
                    "FAILED",
                }
            ),
        },
        "batches": batch_payloads,
        "stages": _stage_counts_payload(
            stage_counts,
        ),
    }


@router.get(
    "/jobs/{job_id}/batches/{batch_id}",
)
async def get_batch_detail(
    job_id: UUID,
    batch_id: UUID,
    query_service: OrchestrationQueryService = Depends(
        get_query_service,
    ),
):
    batch = await query_service.get_batch(
        ingestion_job_id=job_id,
        ingestion_batch_id=batch_id,
    )

    if batch is None:
        raise HTTPException(
            status_code=404,
            detail="Ingestion batch not found",
        )

    documents = await query_service.list_batch_documents(
        ingestion_job_id=job_id,
        ingestion_batch_id=batch_id,
    )

    return {
        "batch": jsonable_encoder(
            asdict(batch),
        ),
        "files": [
            jsonable_encoder(
                asdict(document),
            )
            for document in documents
        ],
    }


@router.get(
    "/jobs/{job_id}/documents/{document_id}",
)
async def get_document_lifecycle(
    job_id: UUID,
    document_id: UUID,
    query_service: OrchestrationQueryService = Depends(
        get_query_service,
    ),
):
    states = await query_service.list_document_stage_states(
        ingestion_job_id=job_id,
        document_id=document_id,
    )

    if not states:
        raise HTTPException(
            status_code=404,
            detail="Ingestion document lifecycle not found",
        )

    return {
        "job_id": str(job_id),
        "document_id": str(document_id),
        "stages": [
            jsonable_encoder(
                asdict(state),
            )
            for state in states
        ],
    }


@router.get(
    "/jobs/{job_id}/events",
)
async def stream_job_events(
    request: Request,
    job_id: UUID,
    after: int = Query(
        0,
        ge=0,
    ),
    last_event_id: str | None = Header(
        default=None,
        alias="Last-Event-ID",
    ),
):
    cursor = after

    if last_event_id:
        try:
            cursor = max(
                cursor,
                int(last_event_id),
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Last-Event-ID must be an integer",
            ) from exc

    async def event_stream() -> AsyncIterator[str]:
        nonlocal cursor

        while True:
            if await request.is_disconnected():
                break

            async with async_session_factory() as session:
                query_service = (
                    create_orchestration_query_service(
                        session=session,
                    )
                )
                events = await query_service.list_events_after(
                    ingestion_job_id=job_id,
                    after=cursor,
                    limit=100,
                )

            if not events:
                await asyncio.sleep(1)
                continue

            for event in events:
                cursor = event.sequence_no
                payload = json.dumps(
                    jsonable_encoder(
                        asdict(event),
                    ),
                )
                yield (
                    f"id: {event.sequence_no}\n"
                    f"event: {event.event_type}\n"
                    f"data: {payload}\n\n"
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
