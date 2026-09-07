from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.application.use_cases.get_enabled_prompt_by_code import (
    GetEnabledPromptByCodeUseCase,
)


class PromptProvider:

    def __init__(
        self,
        get_enabled_prompt_by_code: GetEnabledPromptByCodeUseCase,
    ):
        self._get_enabled_prompt_by_code = (
            get_enabled_prompt_by_code
        )

    async def get_by_code(
        self,
        code: str,
    ) -> PromptDTO | None:

        return await self._get_enabled_prompt_by_code.execute(
            code,
        )
