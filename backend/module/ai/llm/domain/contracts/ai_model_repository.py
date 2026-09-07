from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.ai.llm.domain.entities.ai_model import (
    AIModel,
)


class AIModelRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        model_id: UUID,
    ) -> AIModel | None:
        pass

    @abstractmethod
    async def get_by_provider_and_code(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:
        pass

    @abstractmethod
    async def get(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:
        pass

    @abstractmethod
    async def get_enabled_by_provider_and_code(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModel | None:
        pass

    @abstractmethod
    async def list(
        self,
    ) -> list[AIModel]:
        pass

    @abstractmethod
    async def add(
        self,
        entity: AIModel,
    ) -> AIModel:
        pass

    @abstractmethod
    async def update(
        self,
        entity: AIModel,
    ) -> AIModel:
        pass

    @abstractmethod
    async def delete(
        self,
        model_id: UUID,
    ) -> None:
        pass
