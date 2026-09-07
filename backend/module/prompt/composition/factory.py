from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.prompt.application.services.prompt_admin_service import (
    PromptAdminService,
)
from module.prompt.application.services.prompt_provider import (
    PromptProvider as ApplicationPromptProvider,
)
from module.prompt.composition.prompt_provider import (
    PromptProvider,
)
from module.prompt.application.use_cases.create_prompt import (
    CreatePromptUseCase,
)
from module.prompt.application.use_cases.delete_prompt import (
    DeletePromptUseCase,
)
from module.prompt.application.use_cases.get_enabled_prompt_by_code import (
    GetEnabledPromptByCodeUseCase,
)
from module.prompt.application.use_cases.get_prompt import (
    GetPromptUseCase,
)
from module.prompt.application.use_cases.get_prompt_by_code import (
    GetPromptByCodeUseCase,
)
from module.prompt.application.use_cases.list_prompts import (
    ListPromptsUseCase,
)
from module.prompt.application.use_cases.update_prompt import (
    UpdatePromptUseCase,
)
from module.prompt.infrastructure.persistence.repositories.sqlalchemy_prompt_repository import (
    SqlAlchemyPromptRepository,
)


def create_prompt_provider(
    session: AsyncSession,
) -> PromptProvider:

    repository = SqlAlchemyPromptRepository(
        session=session,
    )

    get_enabled_prompt_by_code = (
        GetEnabledPromptByCodeUseCase(
            repository=repository,
        )
    )

    application_provider = ApplicationPromptProvider(
        get_enabled_prompt_by_code=(
            get_enabled_prompt_by_code
        ),
    )

    return PromptProvider(
        provider=application_provider,
    )


def create_prompt_admin_service(
    session: AsyncSession,
) -> PromptAdminService:

    repository = SqlAlchemyPromptRepository(
        session=session,
    )

    return PromptAdminService(
        create_prompt=CreatePromptUseCase(
            repository=repository,
        ),
        get_prompt=GetPromptUseCase(
            repository=repository,
        ),
        get_prompt_by_code=GetPromptByCodeUseCase(
            repository=repository,
        ),
        list_prompts=ListPromptsUseCase(
            repository=repository,
        ),
        update_prompt=UpdatePromptUseCase(
            repository=repository,
        ),
        delete_prompt=DeletePromptUseCase(
            repository=repository,
        ),
    )
