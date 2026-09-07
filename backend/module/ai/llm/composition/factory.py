from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.ai.llm.application.services.ai_model_admin_service import (
    AIModelAdminService,
)
from module.ai.llm.application.services.ai_model_provider import (
    AIModelProvider as ApplicationAIModelProvider,
)
from module.ai.llm.application.services.ai_provider_admin_service import (
    AIProviderAdminService,
)
from module.ai.llm.application.use_cases.models.create_ai_model import (
    CreateAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.delete_ai_model import (
    DeleteAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.get_ai_model import (
    GetAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.get_ai_model_by_ref import (
    GetAIModelByRefUseCase,
)
from module.ai.llm.application.use_cases.models.list_ai_models import (
    ListAIModelsUseCase,
)
from module.ai.llm.application.use_cases.models.resolve_ai_model import (
    ResolveAIModelUseCase,
)
from module.ai.llm.application.use_cases.models.update_ai_model import (
    UpdateAIModelUseCase,
)
from module.ai.llm.application.use_cases.providers.create_ai_provider import (
    CreateAIProviderUseCase,
)
from module.ai.llm.application.use_cases.providers.delete_ai_provider import (
    DeleteAIProviderUseCase,
)
from module.ai.llm.application.use_cases.providers.get_ai_provider import (
    GetAIProviderUseCase,
)
from module.ai.llm.application.use_cases.providers.get_ai_provider_by_code import (
    GetAIProviderByCodeUseCase,
)
from module.ai.llm.application.use_cases.providers.list_ai_providers import (
    ListAIProvidersUseCase,
)
from module.ai.llm.application.use_cases.providers.update_ai_provider import (
    UpdateAIProviderUseCase,
)
from module.ai.llm.composition.ai_model_provider import (
    AIModelProvider,
)
from module.ai.llm.composition.llm_gateway import (
    LLMGateway,
)
from module.ai.llm.infrastructure.gateways.azure_openai_llm_gateway import (
    AzureOpenAILLMGateway,
)
from module.ai.llm.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from module.ai.llm.infrastructure.persistence.repositories.sqlalchemy_ai_provider_repository import (
    SqlAlchemyAIProviderRepository,
)


def create_ai_model_provider(
    session: AsyncSession,
) -> AIModelProvider:

    return AIModelProvider(
        provider=_create_application_ai_model_provider(
            session,
        ),
    )


def create_llm_gateway(
    session: AsyncSession,
) -> LLMGateway:

    gateway = AzureOpenAILLMGateway(
        ai_model_provider=(
            _create_application_ai_model_provider(
                session,
            )
        ),
    )

    return LLMGateway(
        gateway=gateway,
    )


def create_ai_provider_admin_service(
    session: AsyncSession,
) -> AIProviderAdminService:

    repository = SqlAlchemyAIProviderRepository(
        session=session,
    )

    return AIProviderAdminService(
        create_provider=CreateAIProviderUseCase(
            repository=repository,
        ),
        get_provider=GetAIProviderUseCase(
            repository=repository,
        ),
        get_provider_by_code=GetAIProviderByCodeUseCase(
            repository=repository,
        ),
        list_providers=ListAIProvidersUseCase(
            repository=repository,
        ),
        update_provider=UpdateAIProviderUseCase(
            repository=repository,
        ),
        delete_provider=DeleteAIProviderUseCase(
            repository=repository,
        ),
    )


def create_ai_model_admin_service(
    session: AsyncSession,
) -> AIModelAdminService:

    repository = SqlAlchemyAIModelRepository(
        session=session,
    )

    return AIModelAdminService(
        create_model=CreateAIModelUseCase(
            repository=repository,
        ),
        get_model=GetAIModelUseCase(
            repository=repository,
        ),
        get_model_by_ref=GetAIModelByRefUseCase(
            repository=repository,
        ),
        list_models=ListAIModelsUseCase(
            repository=repository,
        ),
        update_model=UpdateAIModelUseCase(
            repository=repository,
        ),
        delete_model=DeleteAIModelUseCase(
            repository=repository,
        ),
    )


def _create_application_ai_model_provider(
    session: AsyncSession,
) -> ApplicationAIModelProvider:

    provider_repository = SqlAlchemyAIProviderRepository(
        session=session,
    )
    model_repository = SqlAlchemyAIModelRepository(
        session=session,
    )

    return ApplicationAIModelProvider(
        resolve_ai_model=ResolveAIModelUseCase(
            model_repository=model_repository,
            provider_repository=provider_repository,
        ),
    )
