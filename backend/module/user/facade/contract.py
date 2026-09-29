from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from .dto import UserDTO


class UserModuleFacade(
    ABC,
):
    """
    Hop dong cong khai duy nhat cua module user. Module khac (auth, authz)
    CHI duoc import tu day - khong bao gio import thang domain/infra ben
    trong module user.
    """

    @abstractmethod
    async def get_user(
        self,
        user_id: UUID,
    ) -> UserDTO | None:
        pass

    @abstractmethod
    async def get_user_by_email(
        self,
        email: str,
    ) -> UserDTO | None:
        pass

    @abstractmethod
    async def create_user(
        self,
        email: str,
    ) -> UserDTO:
        pass

    @abstractmethod
    async def mark_email_verified(
        self,
        user_id: UUID,
        verified_at: datetime,
    ) -> None:
        pass

    @abstractmethod
    async def activate_external_user(
        self,
        user_id: UUID,
        email_verified_at: datetime | None,
    ) -> None:
        pass
