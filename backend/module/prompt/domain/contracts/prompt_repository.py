from abc import ABC
from abc import abstractmethod
from uuid import UUID

from module.prompt.domain.entities.prompt import (
    Prompt,
)


class PromptRepository(
    ABC,
):

    @abstractmethod
    async def get_by_id(
        self,
        prompt_id: UUID,
    ) -> Prompt | None:
        pass

    @abstractmethod
    async def get_by_code(
        self,
        code: str,
    ) -> Prompt | None:
        pass

    @abstractmethod
    async def get_enabled_by_code(
        self,
        code: str,
    ) -> Prompt | None:
        pass

    @abstractmethod
    async def list(
        self,
    ) -> list[Prompt]:
        pass

    @abstractmethod
    async def add(
        self,
        entity: Prompt,
    ) -> Prompt:
        pass

    @abstractmethod
    async def update(
        self,
        entity: Prompt,
    ) -> Prompt:
        pass

    @abstractmethod
    async def delete(
        self,
        prompt_id: UUID,
    ) -> None:
        pass
