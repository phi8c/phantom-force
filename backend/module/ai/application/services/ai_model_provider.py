from module.ai.application.dtos.ai_model_resolution_dto import (
    AIModelResolutionDTO,
)
from module.ai.application.use_cases.models.resolve_ai_model import (
    ResolveAIModelUseCase,
)


class AIModelProvider:

    def __init__(
        self,
        resolve_ai_model: ResolveAIModelUseCase,
    ):
        self._resolve_ai_model = resolve_ai_model

    async def get(
        self,
        provider_code: str,
        model_code: str,
    ) -> AIModelResolutionDTO | None:

        return await self._resolve_ai_model.execute(
            provider_code=provider_code,
            model_code=model_code,
        )
