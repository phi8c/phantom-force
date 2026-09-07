from uuid import UUID

from module.ai.llm.domain.contracts.ai_model_repository import (
    AIModelRepository,
)


class DeleteAIModelUseCase:

    def __init__(
        self,
        repository: AIModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        model_id: UUID,
    ) -> None:

        await self.repository.delete(
            model_id,
        )
