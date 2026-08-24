from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.auth.domain.entities.identity_link import IdentityLink
from module.auth.domain.enums.auth_provider import AuthProvider


class IdentityLinkRepository(
    ABC,
):

    @abstractmethod
    async def get_by_provider_and_sub(
        self,
        provider: AuthProvider,
        external_sub: str,
    ) -> IdentityLink | None:
        pass

    @abstractmethod
    async def list_by_user_id(
        self,
        user_id: UUID,
    ) -> list[IdentityLink]:
        pass

    @abstractmethod
    async def add(
        self,
        entity: IdentityLink,
    ) -> IdentityLink:
        pass