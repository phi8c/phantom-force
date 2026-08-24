from fastapi import APIRouter

from app.presentation.source.controllers.source_controller import (
    router as source_router,
)
from app.presentation.ingestion.controllers.ingestion_controller import (
    router as ingestion_router,)

api_router = APIRouter()

api_router.include_router(
    source_router,
)
api_router.include_router(
    ingestion_router,)