from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from module.user.domain.contracts.user_repository import (
    UserRepository,
)
from module.user.domain.entities.user import (
    User,
)
from module.user.domain.enums.user_status import (
    UserStatus,
)

from .contract import UserModuleFacade
from .dto import UserDTO
from .exceptions import UserAlreadyExistsError


class LocalUserFacade(
    UserModuleFacade,
):
    """
    Impl goi thang use case/repository cung process - dung khi chua tach
    microservice. Chon boi factory.py theo config.
    """

    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self._users = user_repository

    async def get_user(
        self,
        user_id: UUID,
    ) -> UserDTO | None:

        user = await self._users.get_by_id(
            user_id,
        )

        if user is None:
            return None

        return self._to_dto(
            user,
        )

    async def get_user_by_email(
        self,
        email: str,
    ) -> UserDTO | None:

        user = await self._users.get_by_email(
            email,
        )

        if user is None:
            return None

        return self._to_dto(
            user,
        )

    async def create_user(
        self,
        email: str,
    ) -> UserDTO:

        now = datetime.now(timezone.utc)

        entity = User(
            id=uuid4(),
            email=email,
            status=UserStatus.PENDING_VERIFICATION,
            full_name=None,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

        try:
            created = await self._users.add(entity)
        except IntegrityError as exc:
            raise UserAlreadyExistsError() from exc

        return self._to_dto(
            created,
        )

    async def mark_email_verified(
        self,
        user_id: UUID,
        verified_at: datetime,
    ) -> None:

        user = await self._users.get_by_id(
            user_id,
        )

        if user is None:
            raise ValueError(
                "User not found",
            )

        user.email_verified_at = verified_at

        if user.status == UserStatus.PENDING_VERIFICATION:
            user.status = UserStatus.ACTIVE

        await self._users.update(
            user,
        )

    async def activate_external_user(
        self,
        user_id: UUID,
        email_verified_at: datetime | None,
    ) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        user.status = UserStatus.ACTIVE
        if email_verified_at is not None:
            user.email_verified_at = email_verified_at
        await self._users.update(user)

    @staticmethod
    def _to_dto(
        user: User,
    ) -> UserDTO:

        return UserDTO(
            id=user.id,
            email=user.email,
            status=user.status.value,
            full_name=user.full_name,
            email_verified=user.email_verified_at is not None,
        )
