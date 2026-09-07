from module.ai.llm.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.llm.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class CreateAIProviderUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider: AIProviderDTO,
    ) -> AIProviderDTO:

        created = await self.repository.add(
            provider.to_entity(),
        )

        return AIProviderDTO.from_entity(
            created,
        )
