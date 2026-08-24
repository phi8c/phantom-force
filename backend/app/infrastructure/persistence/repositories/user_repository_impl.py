from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import (
    User,
)
from app.domain.repositories.user_repository import (
    UserRepository,
)

from app.infrastructure.persistence.mappers.user_mapper import (
    UserMapper,
)
from app.infrastructure.persistence.models.user_model import (
    UserModel,
)

from app.shared.repositories.base_repository import (
    BaseRepository,
)


class UserRepositoryImpl(
    BaseRepository[UserModel],
    UserRepository,
):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session=session,
            model=UserModel,
        )

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:

        model = await super().get_by_id(
            user_id,
        )

        if model is None:
            return None

        return UserMapper.to_domain(
            model,
        )

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:

        result = await self.session.execute(
            select(
                UserModel,
            ).where(
                UserModel.email == email,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return UserMapper.to_domain(
            model,
        )

    async def add(
        self,
        entity: User,
    ) -> User:

        model = UserMapper.to_model(
            entity,
        )

        model = await super().add(
            model,
        )

        return UserMapper.to_domain(
            model,
        )

    async def update(
        self,
        entity: User,
    ) -> None:

        model = await super().get_by_id(
            entity.id,
        )

        if model is None:
            raise ValueError(
                "User not found",
            )

        UserMapper.merge_into_model(
            model,
            entity,
        )

        await self.session.flush()