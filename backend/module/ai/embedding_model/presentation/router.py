from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict

from bootstrap.database import async_session_factory
from module.ai.embedding_model.application.services.embedding_model_service import (
    EmbeddingModelService,
)
from module.ai.embedding_model.composition.factory import (
    create_embedding_model_service,
)


class EmbeddingModelSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    provider: str
    dimension: int
    configuration: dict


router = APIRouter(
    prefix="/embedding-models",
    tags=["embedding-models"],
)


async def get_embedding_model_service() -> AsyncIterator[
    EmbeddingModelService
]:
    async with async_session_factory() as session:
        yield create_embedding_model_service(
            session=session,
        )


@router.get(
    "",
    response_model=list[EmbeddingModelSchema],
)
async def list_embedding_models(
    service: EmbeddingModelService = Depends(
        get_embedding_model_service,
    ),
):
    models = await service.list_enabled()

    return [
        {
            "id": model.id,
            "code": model.code,
            "name": model.name,
            "provider": model.provider,
            "dimension": model.dimension,
            "configuration": model.configuration,
        }
        for model in models
    ]
