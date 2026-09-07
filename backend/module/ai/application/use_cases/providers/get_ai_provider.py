from uuid import UUID

from module.ai.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class GetAIProviderUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider_id: UUID,
    ) -> AIProviderDTO | None:

        provider = await self.repository.get_by_id(
            provider_id,
        )

        if provider is None:
            return None

        return AIProviderDTO.from_entity(
            provider,
        )
