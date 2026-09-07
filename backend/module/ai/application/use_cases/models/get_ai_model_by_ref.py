from module.ai.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.domain.contracts.ai_model_repository import (
    AIModelRepository,
)


class GetAIModelByRefUseCase:

    def __init__(
        self,
        repository: AIModelRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModelDTO | None:

        model = await (
            self.repository.get_by_provider_and_code(
                provider_code=provider_code,
                model_code=model_code,
            )
        )

        if model is None:
            return None

        return AIModelDTO.from_entity(
            model,
        )
