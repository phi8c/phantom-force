from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class UpdatePromptUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        prompt: PromptDTO,
    ) -> PromptDTO:

        updated = await self.repository.update(
            prompt.to_entity(),
        )

        return PromptDTO.from_entity(
            updated,
        )
