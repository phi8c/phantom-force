from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class CreatePromptUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        prompt: PromptDTO,
    ) -> PromptDTO:

        created = await self.repository.add(
            prompt.to_entity(),
        )

        return PromptDTO.from_entity(
            created,
        )
