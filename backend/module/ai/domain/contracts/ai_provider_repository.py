from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ai.domain.entities.ai_provider import (
    AIProvider,
)


class AIProviderRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> AIProvider | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> AIProvider | None:
        pass

    @abstractmethod
    async def get_enabled_by_code(
        self,
        code: str,
    ) -> AIProvider | None:
        pass

    @abstractmethod
    async def list(
        self,
    ) -> list[AIProvider]:
        pass

    @abstractmethod
    async def add(
        self,
        entity: AIProvider,
    ) -> AIProvider:
        pass

    @abstractmethod
    async def update(
        self,
        entity: AIProvider,
    ) -> AIProvider:
        pass

    @abstractmethod
    async def delete(
        self,
        provider_id: UUID,
    ) -> None:
        pass
