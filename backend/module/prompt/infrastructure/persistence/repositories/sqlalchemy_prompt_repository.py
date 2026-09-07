from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)
from module.prompt.domain.entities.prompt import (
    Prompt,
)
from module.prompt.infrastructure.persistence.mappers.prompt_mapper import (
    PromptMapper,
)
from module.prompt.infrastructure.persistence.models.prompt_model import (
    PromptModel,
)
from shared.repositories.base_repository import (
    BaseRepository,
)


class SqlAlchemyPromptRepository(
    BaseRepository[PromptModel],
    PromptRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=PromptModel,
        )

    async def get_by_id(
        self,
        prompt_id: UUID,
    ) -> Prompt | None:

        model = await super().get_by_id(
            prompt_id,
        )

        if model is None:
            return None

        return PromptMapper.to_entity(
            model,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> Prompt | None:

        result = await self.session.execute(
            select(
                PromptModel,
            ).where(
                PromptModel.code == code,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return PromptMapper.to_entity(
            model,
        )

    async def get_enabled_by_code(
        self,
        code: str,
    ) -> Prompt | None:

        result = await self.session.execute(
            select(
                PromptModel,
            ).where(
                PromptModel.code == code,
                PromptModel.enabled.is_(True),
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return PromptMapper.to_entity(
            model,
        )

    async def list(
        self,
    ) -> list[Prompt]:

        models = await super().get_all()

        return [
            PromptMapper.to_entity(
                model,
            )
            for model in models
        ]

    async def add(
        self,
        entity: Prompt,
    ) -> Prompt:

        model = PromptMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return PromptMapper.to_entity(
            model,
        )

    async def update(
        self,
        entity: Prompt,
    ) -> Prompt:

        if entity.id is None:
            raise ValueError(
                "Prompt id is required",
            )

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "Prompt not found",
            )

        PromptMapper.merge_into_model(
            model,
            entity,
        )

        await self.session.flush()
        await self.session.refresh(
            model,
        )

        return PromptMapper.to_entity(
            model,
        )

    async def delete(
        self,
        prompt_id: UUID,
    ) -> None:

        model = await super().get_by_id(
            prompt_id,
        )

        if model is None:
            raise ValueError(
                "Prompt not found",
            )

        await super().delete(
            model,
        )
