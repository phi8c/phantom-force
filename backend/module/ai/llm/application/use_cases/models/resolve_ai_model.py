from module.ai.llm.application.dtos.ai_model_resolution_dto import (
    AIModelResolutionDTO,
)
from module.ai.llm.application.dtos.ai_model_dto import (
    AIModelDTO,
)
from module.ai.llm.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.llm.domain.contracts.ai_model_repository import (
    AIModelRepository,
)
from module.ai.llm.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class ResolveAIModelUseCase:

    def __init__(
        self,
        model_repository: AIModelRepository,
        provider_repository: AIProviderRepository,
    ):
        self.model_repository = model_repository
        self.provider_repository = provider_repository

    async def execute(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModelResolutionDTO | None:

        provider = await (
            self.provider_repository.get_enabled_by_code(
                provider_code,
            )
        )

        if provider is None:
            return None

        model = await (
            self.model_repository.get(
                provider_code=provider_code,
                model_code=model_code,
            )
        )

        if model is None:
            return None

        return AIModelResolutionDTO(
            provider=AIProviderDTO.from_entity(
                provider,
            ),
            model=AIModelDTO.from_entity(
                model,
            ),
        )
