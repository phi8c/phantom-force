from uuid import UUID

from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class DeletePromptUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        prompt_id: UUID,
    ) -> None:

        await self.repository.delete(
            prompt_id,
        )
