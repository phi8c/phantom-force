from module.ai.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class ListAIProvidersUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
    ) -> list[AIProviderDTO]:

        providers = await self.repository.list()

        return [
            AIProviderDTO.from_entity(
                provider,
            )
            for provider in providers
        ]
