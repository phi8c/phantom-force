from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from module.auth.domain.entities.management_auth_policy import ManagementAuthPolicy


class ManagementAuthPolicyRepository(ABC):
    @abstractmethod
    async def get_active(self) -> ManagementAuthPolicy | None:
        pass

    @abstractmethod
    async def get_by_id(self, policy_id: UUID) -> ManagementAuthPolicy | None:
        pass

    @abstractmethod
    async def add(self, policy: ManagementAuthPolicy) -> ManagementAuthPolicy:
        pass

    @abstractmethod
    async def update(self, policy: ManagementAuthPolicy) -> None:
        pass
