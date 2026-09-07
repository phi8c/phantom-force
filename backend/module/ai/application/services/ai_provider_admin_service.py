from uuid import UUID

from module.ai.application.dtos.ai_provider_dto import (
    AIProviderDTO,
)
from module.ai.application.use_cases.providers.create_ai_provider import (
    CreateAIProviderUseCase,
)
from module.ai.application.use_cases.providers.delete_ai_provider import (
    DeleteAIProviderUseCase,
)
from module.ai.application.use_cases.providers.get_ai_provider import (
    GetAIProviderUseCase,
)
from module.ai.application.use_cases.providers.get_ai_provider_by_code import (
    GetAIProviderByCodeUseCase,
)
from module.ai.application.use_cases.providers.list_ai_providers import (
    ListAIProvidersUseCase,
)
from module.ai.application.use_cases.providers.update_ai_provider import (
    UpdateAIProviderUseCase,
)


class AIProviderAdminService:

    def __init__(
        self,
        create_provider: CreateAIProviderUseCase,
        get_provider: GetAIProviderUseCase,
        get_provider_by_code: GetAIProviderByCodeUseCase,
        list_providers: ListAIProvidersUseCase,
        update_provider: UpdateAIProviderUseCase,
        delete_provider: DeleteAIProviderUseCase,
    ):
        self._create_provider = create_provider
        self._get_provider = get_provider
        self._get_provider_by_code = get_provider_by_code
        self._list_providers = list_providers
        self._update_provider = update_provider
        self._delete_provider = delete_provider

    async def create(
        self,
        provider: AIProviderDTO,
    ) -> AIProviderDTO:

        return await self._create_provider.execute(
            provider,
        )

    async def get_by_id(
        self,
        provider_id: UUID,
    ) -> AIProviderDTO | None:

        return await self._get_provider.execute(
            provider_id,
        )

    async def get_by_code(
        self,
        code: str,
    ) -> AIProviderDTO | None:

        return await self._get_provider_by_code.execute(
            code,
        )

    async def list(
        self,
    ) -> list[AIProviderDTO]:

        return await self._list_providers.execute()

    async def update(
        self,
        provider: AIProviderDTO,
    ) -> AIProviderDTO:

        return await self._update_provider.execute(
            provider,
        )

    async def delete(
        self,
        provider_id: UUID,
    ) -> None:

        await self._delete_provider.execute(
            provider_id,
        )
