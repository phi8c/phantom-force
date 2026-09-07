from module.ai.application.dtos.ai_model_resolution_dto import (
    AIModelResolutionDTO,
)
from module.ai.application.services.ai_model_provider import (
    AIModelProvider as ApplicationAIModelProvider,
)
from module.ai.composition.ai_model_ref import (
    AIModelRef,
)


class AIModelProvider:

    def __init__(
        self,
        provider: ApplicationAIModelProvider,
    ):
        self._provider = provider

    async def get(
        self,
        provider_code: str | None = None,
        model_code: str | None = None,
        model_ref: AIModelRef | None = None,
    ) -> AIModelResolutionDTO | None:

        if model_ref is not None:
            provider_code = model_ref.provider_code
            model_code = model_ref.model_code

        if provider_code is None or model_code is None:
            raise ValueError(
                "provider_code and model_code are required",
            )

        return await self._provider.get(
            provider_code=provider_code,
            model_code=model_code,
        )
