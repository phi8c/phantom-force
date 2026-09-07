from module.ai.llm.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.llm.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class GetAIProviderByCodeUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        code: str,
    ) -> AIProviderDTO | None:

        provider = await self.repository.get_by_code(
            code,
        )

        if provider is None:
            return None

        return AIProviderDTO.from_entity(
            provider,
        )
