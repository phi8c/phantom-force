from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class ListPromptsUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[PromptDTO]:

        prompts = await self.repository.list()

        return [
            PromptDTO.from_entity(
                prompt,
            )
            for prompt in prompts
        ]
