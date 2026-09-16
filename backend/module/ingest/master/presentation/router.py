from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict

from bootstrap.database import async_session_factory
from module.ingest.master.chunking_strategy.application.services.chunking_strategy_service import (
    ChunkingStrategyService,
)
from module.ingest.master.chunking_strategy.composition.factory import (
    create_chunking_strategy_service,
)
from module.ingest.master.extraction_strategy.application.services.extraction_strategy_service import (
    ExtractionStrategyService,
)
from module.ingest.master.extraction_strategy.composition.factory import (
    create_extraction_strategy_service,
)


class ExtractionEngineSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    provider: str
    configuration: dict


class ChunkingStrategySchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str
    name: str
    configuration: dict


router = APIRouter(
    prefix="/ingest/master",
    tags=["ingest-master"],
)


async def get_extraction_strategy_service() -> AsyncIterator[
    ExtractionStrategyService
]:
    async with async_session_factory() as session:
        yield create_extraction_strategy_service(
            session=session,
        )


async def get_chunking_strategy_service() -> AsyncIterator[
    ChunkingStrategyService
]:
    async with async_session_factory() as session:
        yield create_chunking_strategy_service(
            session=session,
        )


@router.get(
    "/extraction-engines",
    response_model=list[ExtractionEngineSchema],
)
async def list_extraction_engines(
    service: ExtractionStrategyService = Depends(
        get_extraction_strategy_service,
    ),
):
    strategies = await service.list_enabled()

    return [
        {
            "id": strategy.id,
            "code": strategy.code,
            "name": strategy.name,
            "provider": strategy.provider,
            "configuration": strategy.configuration,
        }
        for strategy in strategies
    ]


@router.get(
    "/chunking-strategies",
    response_model=list[ChunkingStrategySchema],
)
async def list_chunking_strategies(
    service: ChunkingStrategyService = Depends(
        get_chunking_strategy_service,
    ),
):
    strategies = await service.list_enabled()

    return [
        {
            "id": strategy.id,
            "code": strategy.code,
            "name": strategy.name,
            "configuration": strategy.configuration,
        }
        for strategy in strategies
    ]
