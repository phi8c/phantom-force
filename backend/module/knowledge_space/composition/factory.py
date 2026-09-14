from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from module.enterprise.infrastructure.persistence.repositories.enterprise_repository_impl import (
    EnterpriseRepositoryImpl,
)
from module.ai.embedding_model.infrastructure.persistence.repositories.embedding_model_repository_impl import (
    EmbeddingModelRepositoryImpl,
)
from module.master_data.data_hub_providers.infrastructure.persistence.repositories.data_hub_provider_repository_impl import (
    DataHubProviderRepositoryImpl,
)
from module.knowledge_space.application.services.knowledge_space_service import (
    KnowledgeSpaceService,
)
from module.knowledge_space.application.use_cases.create_knowledge_space import (
    CreateKnowledgeSpaceUseCase,
)
from module.knowledge_space.application.use_cases.get_data_hub_config import (
    GetKnowledgeSpaceDataHubUseCase,
)
from module.knowledge_space.application.use_cases.get_embedding_config import (
    GetKnowledgeSpaceEmbeddingConfigUseCase,
)
from module.knowledge_space.application.use_cases.get_knowledge_space import (
    GetKnowledgeSpaceUseCase,
)
from module.knowledge_space.application.use_cases.list_knowledge_spaces import (
    ListKnowledgeSpacesUseCase,
)
from module.knowledge_space.application.use_cases.save_data_hub_config import (
    SaveKnowledgeSpaceDataHubConfigUseCase,
)
from module.knowledge_space.application.use_cases.save_embedding_config import (
    SaveKnowledgeSpaceEmbeddingConfigUseCase,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_data_hub_repository_impl import (
    KnowledgeSpaceDataHubRepositoryImpl,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_embedding_config_repository_impl import (
    KnowledgeSpaceEmbeddingConfigRepositoryImpl,
)
from module.knowledge_space.infrastructure.persistence.repositories.knowledge_space_repository_impl import (
    KnowledgeSpaceRepositoryImpl,
)


def create_knowledge_space(
    session: AsyncSession,
) -> KnowledgeSpaceService:

    repository = KnowledgeSpaceRepositoryImpl(
        session=session,
    )
    data_hub_repository = (
        KnowledgeSpaceDataHubRepositoryImpl(
            session=session,
        )
    )
    embedding_config_repository = (
        KnowledgeSpaceEmbeddingConfigRepositoryImpl(
            session=session,
        )
    )
    enterprise_repository = EnterpriseRepositoryImpl(
        session=session,
    )
    data_hub_provider_repository = (
        DataHubProviderRepositoryImpl(
            session=session,
        )
    )
    embedding_model_repository = (
        EmbeddingModelRepositoryImpl(
            session=session,
        )
    )

    get_knowledge_space = (
        GetKnowledgeSpaceUseCase(
            repository=repository,
        )
    )
    create_knowledge_space = (
        CreateKnowledgeSpaceUseCase(
            repository=repository,
        )
    )
    list_knowledge_spaces = (
        ListKnowledgeSpacesUseCase(
            repository=repository,
        )
    )

    get_data_hub_config = (
        GetKnowledgeSpaceDataHubUseCase(
            repository=data_hub_repository,
        )
    )

    get_embedding_config = (
        GetKnowledgeSpaceEmbeddingConfigUseCase(
            repository=embedding_config_repository,
        )
    )
    save_data_hub_config = (
        SaveKnowledgeSpaceDataHubConfigUseCase(
            repository=data_hub_repository,
        )
    )
    save_embedding_config = (
        SaveKnowledgeSpaceEmbeddingConfigUseCase(
            repository=embedding_config_repository,
        )
    )

    return KnowledgeSpaceService(
        get_knowledge_space=get_knowledge_space,
        get_data_hub_config=get_data_hub_config,
        get_embedding_config=get_embedding_config,
        create_knowledge_space=create_knowledge_space,
        list_knowledge_spaces=list_knowledge_spaces,
        save_data_hub_config=save_data_hub_config,
        save_embedding_config=save_embedding_config,
        knowledge_space_repository=repository,
        enterprise_repository=enterprise_repository,
        data_hub_provider_repository=(
            data_hub_provider_repository
        ),
        embedding_model_repository=(
            embedding_model_repository
        ),
        session=session,
    )
