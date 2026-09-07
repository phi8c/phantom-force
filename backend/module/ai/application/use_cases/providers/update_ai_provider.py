from module.ai.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class UpdateAIProviderUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider: AIProviderDTO,
    ) -> AIProviderDTO:

        updated = await self.repository.update(
            provider.to_entity(),
        )

        return AIProviderDTO.from_entity(
            updated,
        )
