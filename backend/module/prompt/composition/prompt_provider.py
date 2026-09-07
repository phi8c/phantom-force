from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.application.services.prompt_provider import (
    PromptProvider as ApplicationPromptProvider,
)


class PromptProvider:

    def __init__(
        self,
        provider: ApplicationPromptProvider,
    ):
        self._provider = provider

    async def get_by_code(
        self,
        code: str,
    ) -> PromptDTO | None:

        return await self._provider.get_by_code(
            code,
        )
