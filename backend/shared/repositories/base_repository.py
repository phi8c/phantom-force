from typing import Generic
from typing import TypeVar
from uuid import UUID

from sqlalchemy import exists
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(
    Generic[ModelType],
):
    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    async def get_by_id(
        self,
        entity_id: UUID,
    ) -> ModelType | None:

        result = await self.session.execute(
            select(
                self.model,
            ).where(
                self.model.id == entity_id,
            ),
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
    ) -> list[ModelType]:

        result = await self.session.execute(
            select(
                self.model,
            ),
        )

        return list(
            result.scalars().all(),
        )

    async def exists(
        self,
        entity_id: UUID,
    ) -> bool:

        result = await self.session.execute(
            select(
                exists().where(
                    self.model.id == entity_id,
                ),
            ),
        )

        return bool(
            result.scalar(),
        )

    async def add(
        self,
        model: ModelType,
    ) -> ModelType:

        self.session.add(
            model,
        )

        await self.session.flush()

        await self.session.refresh(
            model,
        )

        return model

    async def delete(
        self,
        model: ModelType,
    ) -> None:

        await self.session.delete(
            model,
        )

        await self.session.flush()