from abc import ABC
from abc import abstractmethod
from uuid import UUID

from app.domain.entities.user import (
    User,
)


class UserRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        pass

    @abstractmethod
    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        pass

    @abstractmethod
    async def add(
        self,
        entity: User,
    ) -> User:
        pass

    @abstractmethod
    async def update(
        self,
        entity: User,
    ) -> None:
        pass