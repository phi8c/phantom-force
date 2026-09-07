from module.ai.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.domain.contracts.ai_model_repository import (
    AIModelRepository,
)


class UpdateAIModelUseCase:

    def __init__(
        self,
        repository: AIModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        model: AIModelDTO,
    ) -> AIModelDTO:

        updated = await self.repository.update(
            model.to_entity(),
        )

        return AIModelDTO.from_entity(
            updated,
        )
