from uuid import UUID

from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class GetPromptUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        prompt_id: UUID,
    ) -> PromptDTO | None:

        prompt = await self.repository.get_by_id(
            prompt_id,
        )

        if prompt is None:
            return None

        return PromptDTO.from_entity(
            prompt,
        )
