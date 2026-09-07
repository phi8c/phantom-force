from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.domain.contracts.prompt_repository import (
    PromptRepository,
)


class GetPromptByCodeUseCase:

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        code: str,
    ) -> PromptDTO | None:

        prompt = await self.repository.get_by_code(
            code,
        )

        if prompt is None:
            return None

        return PromptDTO.from_entity(
            prompt,
        )
