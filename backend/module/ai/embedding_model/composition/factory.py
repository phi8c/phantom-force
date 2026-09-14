from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.ai.embedding_model.application.services.embedding_model_service import (
    EmbeddingModelService,
)
from module.ai.embedding_model.application.use_cases.get_embedding_model import (
    GetEmbeddingModelUseCase,
)
from module.ai.embedding_model.application.use_cases.get_embedding_model_by_code import (
    GetEmbeddingModelByCodeUseCase,
)
from module.ai.embedding_model.application.use_cases.list_embedding_models import (
    ListEmbeddingModelsUseCase,
)
from module.ai.embedding_model.infrastructure.persistence.repositories.embedding_model_repository_impl import (
    EmbeddingModelRepositoryImpl,
)


def create_embedding_model_service(
    session: AsyncSession,
) -> EmbeddingModelService:

    repository = EmbeddingModelRepositoryImpl(
        session=session,
    )

    get_embedding_model = GetEmbeddingModelUseCase(
        repository=repository,
    )

    get_embedding_model_by_code = (
        GetEmbeddingModelByCodeUseCase(
            repository=repository,
        )
    )

    list_embedding_models = ListEmbeddingModelsUseCase(
        repository=repository,
    )

    return EmbeddingModelService(
        get_embedding_model=get_embedding_model,
        get_embedding_model_by_code=(
            get_embedding_model_by_code
        ),
        list_embedding_models=list_embedding_models,
    )
