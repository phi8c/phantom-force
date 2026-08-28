from uuid import UUID

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from bootstrap.queues import (
    create_ingest_dispatchers,
    create_ingest_queue_clients,
)


router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
)


class StartIngestionRequest(BaseModel):
    batch_size: int = 1000


@router.post(
    "/jobs/{ingestion_job_id}/start",
)
async def start_ingestion(
    ingestion_job_id: UUID,
    request: StartIngestionRequest,
):
    if request.batch_size <= 0:
        raise HTTPException(
            status_code=400,
            detail="batch_size must be greater than 0",
        )

    queues = create_ingest_queue_clients()

    try:
        dispatchers = create_ingest_dispatchers(
            queues,
        )

        await dispatchers.discovery.dispatch(
            ingestion_job_id=ingestion_job_id,
            batch_size=request.batch_size,
        )

        return {
            "ingestion_job_id": str(
                ingestion_job_id
            ),
            "status": "QUEUED",
        }

    finally:
        for client in (
            queues.discovery,
            queues.download,
            queues.extraction,
            queues.chunking,
            queues.embedding,
            queues.classification,
        ):
            close = getattr(
                client,
                "close",
                None,
            )

            if close is not None:
                await close()