from collections.abc import AsyncIterator
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi.encoders import jsonable_encoder

from bootstrap.database import async_session_factory
from module.enterprise.application.dtos import (
    CreateEnterpriseRequest,
    ListEnterprisesRequest,
    UpdateEnterpriseRequest,
)
from module.enterprise.application.services import EnterpriseService
from module.enterprise.infrastructure.persistence.repositories.enterprise_repository_impl import (
    EnterpriseRepositoryImpl,
)
from module.enterprise.presentation.schemas import (
    CreateEnterpriseSchema,
    EnterpriseOptionSchema,
    EnterpriseListSchema,
    EnterpriseSchema,
    UpdateEnterpriseSchema,
)


router = APIRouter(
    prefix="/enterprises",
    tags=["enterprises"],
)


async def get_enterprise_service() -> AsyncIterator[
    EnterpriseService
]:
    async with async_session_factory() as session:
        yield EnterpriseService(
            repository=EnterpriseRepositoryImpl(
                session=session,
            ),
            session=session,
        )


@router.post(
    "",
    response_model=EnterpriseSchema,
    status_code=201,
)
async def create_enterprise(
    request: CreateEnterpriseSchema,
    service: EnterpriseService = Depends(
        get_enterprise_service,
    ),
):
    try:
        response = await service.create(
            CreateEnterpriseRequest(
                code=request.code.strip(),
                name=request.name.strip(),
                description=request.description,
                status=request.status,
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
    "/options",
    response_model=list[EnterpriseOptionSchema],
)
async def list_enterprise_options(
    service: EnterpriseService = Depends(
        get_enterprise_service,
    ),
):
    responses = await service.list_enabled()

    return [
        {
            "id": response.id,
            "code": response.code,
            "name": response.name,
        }
        for response in responses
    ]


@router.get(
    "",
    response_model=EnterpriseListSchema,
)
async def list_enterprises(
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    cursor: str | None = Query(
        None,
    ),
    service: EnterpriseService = Depends(
        get_enterprise_service,
    ),
):
    try:
        response = await service.list_page(
            ListEnterprisesRequest(
                limit=limit,
                cursor=cursor,
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
    "/{enterprise_id}",
    response_model=EnterpriseSchema,
)
async def get_enterprise(
    enterprise_id: UUID,
    service: EnterpriseService = Depends(
        get_enterprise_service,
    ),
):
    response = await service.get(
        enterprise_id,
    )

    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Enterprise not found",
        )

    return jsonable_encoder(
        asdict(response),
    )


@router.patch(
    "/{enterprise_id}",
    response_model=EnterpriseSchema,
)
async def update_enterprise(
    enterprise_id: UUID,
    request: UpdateEnterpriseSchema,
    service: EnterpriseService = Depends(
        get_enterprise_service,
    ),
):
    try:
        response = await service.update(
            enterprise_id,
            UpdateEnterpriseRequest(
                code=(
                    request.code.strip()
                    if request.code is not None
                    else None
                ),
                name=(
                    request.name.strip()
                    if request.name is not None
                    else None
                ),
                description=request.description,
                description_provided=(
                    "description"
                    in request.model_fields_set
                ),
                status=request.status,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Enterprise not found",
        )

    return jsonable_encoder(
        asdict(response),
    )
