from collections.abc import AsyncIterator
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi.encoders import jsonable_encoder

from bootstrap.database import async_session_factory
from module.knowledge_space.application.dtos import (
    CreateKnowledgeSpaceRequest,
    ListKnowledgeSpacesRequest,
    SaveDataHubConfigRequest,
    SaveEmbeddingConfigRequest,
)
from module.knowledge_space.application.services.knowledge_space_service import (
    KnowledgeSpaceService,
)
from module.knowledge_space.composition.factory import (
    create_knowledge_space,
)
from module.knowledge_space.presentation.schemas import (
    CreateKnowledgeSpaceSchema,
    KnowledgeSpaceDataHubEnvelopeSchema,
    KnowledgeSpaceDataHubSchema,
    KnowledgeSpaceEmbeddingEnvelopeSchema,
    KnowledgeSpaceEmbeddingSchema,
    KnowledgeSpaceListSchema,
    KnowledgeSpaceSchema,
    SaveDataHubConfigSchema,
    SaveEmbeddingConfigSchema,
)


router = APIRouter(
    prefix="/knowledge-spaces",
    tags=["knowledge-spaces"],
)


async def get_knowledge_space_service() -> AsyncIterator[
    KnowledgeSpaceService
]:
    async with async_session_factory() as session:
        yield create_knowledge_space(
            session=session,
        )


@router.post(
    "",
    response_model=KnowledgeSpaceSchema,
    status_code=201,
)
async def create_knowledge_space_endpoint(
    request: CreateKnowledgeSpaceSchema,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.create_knowledge_space(
            CreateKnowledgeSpaceRequest(
                enterprise_id=request.enterprise_id,
                name=request.name.strip(),
                code=request.code.strip(),
                description=request.description,
                configuration=request.configuration,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )


@router.get(
    "",
    response_model=KnowledgeSpaceListSchema,
)
async def list_knowledge_spaces_endpoint(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    enterprise_id: UUID | None = Query(
        None,
    ),
    search: str | None = Query(
        None,
    ),
    status: str | None = Query(
        None,
    ),
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.list_knowledge_spaces(
            ListKnowledgeSpacesRequest(
                page=page,
                page_size=page_size,
                enterprise_id=enterprise_id,
                search=search,
                status=status,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )


@router.get(
    "/{knowledge_space_id}",
    response_model=KnowledgeSpaceSchema,
)
async def get_knowledge_space_endpoint(
    knowledge_space_id: UUID,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    response = await service.get_knowledge_space(
        knowledge_space_id,
    )

    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge space not found",
        )

    return jsonable_encoder(
        asdict(response),
    )


@router.get(
    "/{knowledge_space_id}/data-hub",
    response_model=KnowledgeSpaceDataHubEnvelopeSchema,
)
async def get_data_hub_config_endpoint(
    knowledge_space_id: UUID,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.get_data_hub_config(
            knowledge_space_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )


@router.put(
    "/{knowledge_space_id}/data-hub",
    response_model=KnowledgeSpaceDataHubSchema,
)
async def save_data_hub_config_endpoint(
    knowledge_space_id: UUID,
    request: SaveDataHubConfigSchema,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.save_data_hub_config(
            knowledge_space_id,
            SaveDataHubConfigRequest(
                data_hub_provider_id=(
                    request.data_hub_provider_id
                ),
                configuration=request.configuration,
                enabled=request.enabled,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                404
                if str(exc) == "Knowledge space not found"
                else 400
            ),
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )


@router.get(
    "/{knowledge_space_id}/embedding",
    response_model=KnowledgeSpaceEmbeddingEnvelopeSchema,
)
async def get_embedding_config_endpoint(
    knowledge_space_id: UUID,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.get_embedding_config(
            knowledge_space_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )


@router.put(
    "/{knowledge_space_id}/embedding",
    response_model=KnowledgeSpaceEmbeddingSchema,
)
async def save_embedding_config_endpoint(
    knowledge_space_id: UUID,
    request: SaveEmbeddingConfigSchema,
    service: KnowledgeSpaceService = Depends(
        get_knowledge_space_service,
    ),
):
    try:
        response = await service.save_embedding_config(
            knowledge_space_id,
            SaveEmbeddingConfigRequest(
                embedding_model_id=request.embedding_model_id,
                configuration=request.configuration,
                enabled=request.enabled,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                404
                if str(exc) == "Knowledge space not found"
                else 400
            ),
            detail=str(exc),
        ) from exc

    return jsonable_encoder(
        asdict(response),
    )
