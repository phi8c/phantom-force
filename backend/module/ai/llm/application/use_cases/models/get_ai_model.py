from uuid import UUID

from module.ai.llm.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.llm.domain.contracts.ai_model_repository import (
    AIModelRepository,
)


class GetAIModelUseCase:

    def __init__(
        self,
        repository: AIModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        model_id: UUID,
    ) -> AIModelDTO | None:

        model = await self.repository.get_by_id(
            model_id,
        )

        if model is None:
            return None

        return AIModelDTO.from_entity(
            model,
        )
