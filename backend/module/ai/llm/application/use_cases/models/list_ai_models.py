from module.ai.llm.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.llm.domain.contracts.ai_model_repository import (
    AIModelRepository,
)


class ListAIModelsUseCase:

    def __init__(
        self,
        repository: AIModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[AIModelDTO]:

        models = await self.repository.list()

        return [
            AIModelDTO.from_entity(
                model,
            )
            for model in models
        ]
