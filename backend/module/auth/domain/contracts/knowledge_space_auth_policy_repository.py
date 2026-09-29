from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from module.auth.domain.entities.knowledge_space_auth_policy import (
    KnowledgeSpaceAuthPolicy,
)


class KnowledgeSpaceAuthPolicyRepository(ABC):
    @abstractmethod
    async def get_by_knowledge_space_id(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceAuthPolicy | None:
        pass

    @abstractmethod
    async def add(
        self,
        policy: KnowledgeSpaceAuthPolicy,
    ) -> KnowledgeSpaceAuthPolicy:
        pass

    @abstractmethod
    async def update(self, policy: KnowledgeSpaceAuthPolicy) -> None:
        pass
