from uuid import UUID

from module.prompt.application.dtos.prompt_dto import (
    PromptDTO,
)
from module.prompt.application.use_cases.create_prompt import (
    CreatePromptUseCase,
)
from module.prompt.application.use_cases.delete_prompt import (
    DeletePromptUseCase,
)
from module.prompt.application.use_cases.get_prompt import (
    GetPromptUseCase,
)
from module.prompt.application.use_cases.get_prompt_by_code import (
    GetPromptByCodeUseCase,
)
from module.prompt.application.use_cases.list_prompts import (
    ListPromptsUseCase,
)
from module.prompt.application.use_cases.update_prompt import (
    UpdatePromptUseCase,
)


class PromptAdminService:

    def __init__(
        self,
        create_prompt: CreatePromptUseCase,
        get_prompt: GetPromptUseCase,
        get_prompt_by_code: GetPromptByCodeUseCase,
        list_prompts: ListPromptsUseCase,
        update_prompt: UpdatePromptUseCase,
        delete_prompt: DeletePromptUseCase,
    ):
        self._create_prompt = create_prompt
        self._get_prompt = get_prompt
        self._get_prompt_by_code = get_prompt_by_code
        self._list_prompts = list_prompts
        self._update_prompt = update_prompt
        self._delete_prompt = delete_prompt

    async def create(
        self,
        prompt: PromptDTO,
    ) -> PromptDTO:

        return await self._create_prompt.execute(
            prompt,
        )

    async def get_by_id(
        self,
        prompt_id: UUID,
    ) -> PromptDTO | None:

        return await self._get_prompt.execute(
            prompt_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> PromptDTO | None:

        return await self._get_prompt_by_code.execute(
            code,
        )

    async def list(
        self,
    ) -> list[PromptDTO]:

        return await self._list_prompts.execute()

    async def update(
        self,
        prompt: PromptDTO,
    ) -> PromptDTO:

        return await self._update_prompt.execute(
            prompt,
        )

    async def delete(
        self,
        prompt_id: UUID,
    ) -> None:

        await self._delete_prompt.execute(
            prompt_id,
        )
