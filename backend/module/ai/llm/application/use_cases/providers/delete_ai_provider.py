from uuid import UUID

from module.ai.llm.domain.contracts.ai_provider_repository import (
    AIProviderRepository,
)


class DeleteAIProviderUseCase:

    def __init__(
        self,
        repository: AIProviderRepository,
    ):
        self.repository = repository

    async def execute(
        self,
        provider_id: UUID,
    ) -> None:

        await self.repository.delete(
            provider_id,
        )
