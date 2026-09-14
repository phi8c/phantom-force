from uuid import UUID

from sqlalchemy.exc import IntegrityError

from module.enterprise.domain.contracts.enterprise_repository import (
    EnterpriseRepository,
)
from module.ai.embedding_model.domain.contracts.embedding_model_repository import (
    EmbeddingModelRepository,
)
from module.master_data.data_hub_providers.domain.contracts.data_hub_provider_repository import (
    DataHubProviderRepository,
)
from module.knowledge_space.application.dtos import (
    CreateKnowledgeSpaceRequest,
    KnowledgeSpaceDataHubConfigResponse,
    KnowledgeSpaceDataHubResponse,
    KnowledgeSpaceEmbeddingConfigEnvelopeResponse,
    KnowledgeSpaceEmbeddingConfigResponse,
    KnowledgeSpaceListItemResponse,
    KnowledgeSpaceResponse,
    ListKnowledgeSpacesRequest,
    ListKnowledgeSpacesResponse,
    SaveDataHubConfigRequest,
    SaveEmbeddingConfigRequest,
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
from module.knowledge_space.domain.contracts.knowledge_space_repository import (
    KnowledgeSpaceRepository,
)

from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)
from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)
from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)


class KnowledgeSpaceService:

    def __init__(
        self,
        get_knowledge_space: GetKnowledgeSpaceUseCase,
        get_data_hub_config: GetKnowledgeSpaceDataHubUseCase,
        get_embedding_config: GetKnowledgeSpaceEmbeddingConfigUseCase,
        create_knowledge_space: CreateKnowledgeSpaceUseCase,
        list_knowledge_spaces: ListKnowledgeSpacesUseCase,
        save_data_hub_config: SaveKnowledgeSpaceDataHubConfigUseCase,
        save_embedding_config: SaveKnowledgeSpaceEmbeddingConfigUseCase,
        knowledge_space_repository: KnowledgeSpaceRepository,
        enterprise_repository: EnterpriseRepository,
        data_hub_provider_repository: DataHubProviderRepository,
        embedding_model_repository: EmbeddingModelRepository,
        session,
    ):
        self._get_knowledge_space = (
            get_knowledge_space
        )

        self._get_data_hub_config = (
            get_data_hub_config
        )

        self._get_embedding_config = (
            get_embedding_config
        )
        self._create_knowledge_space = (
            create_knowledge_space
        )
        self._list_knowledge_spaces = (
            list_knowledge_spaces
        )
        self._save_data_hub_config = (
            save_data_hub_config
        )
        self._save_embedding_config = (
            save_embedding_config
        )
        self._knowledge_space_repository = (
            knowledge_space_repository
        )
        self._enterprise_repository = (
            enterprise_repository
        )
        self._data_hub_provider_repository = (
            data_hub_provider_repository
        )
        self._embedding_model_repository = (
            embedding_model_repository
        )
        self._session = session

    async def create_knowledge_space(
        self,
        request: CreateKnowledgeSpaceRequest,
    ) -> KnowledgeSpaceResponse:

        self._validate_code(
            request.code,
        )
        self._validate_name(
            request.name,
        )

        enterprise = await self._enterprise_repository.get_by_id(
            request.enterprise_id,
        )

        if enterprise is None:
            raise ValueError(
                "Enterprise not found"
            )

        existing = await self._knowledge_space_repository.get_by_code(
            request.code,
        )

        if existing is not None:
            raise ValueError(
                "Knowledge space code already exists"
            )

        try:
            knowledge_space = (
                await self._create_knowledge_space.execute(
                    KnowledgeSpace(
                        id=None,
                        enterprise_id=request.enterprise_id,
                        name=request.name,
                        code=request.code,
                        description=request.description,
                        status="ACTIVE",
                        configuration=request.configuration or {},
                        created_at=None,
                        updated_at=None,
                    )
                )
            )

            await self._session.commit()

        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError(
                "Knowledge space code already exists"
            ) from exc

        return self._to_response(
            knowledge_space,
        )

    async def list_knowledge_spaces(
        self,
        request: ListKnowledgeSpacesRequest,
    ) -> ListKnowledgeSpacesResponse:

        if request.page < 1:
            raise ValueError(
                "page must be greater than or equal to 1"
            )

        if request.page_size < 1 or request.page_size > 100:
            raise ValueError(
                "page_size must be between 1 and 100"
            )

        search = (
            request.search.strip()
            if request.search and request.search.strip()
            else None
        )
        status = (
            request.status.strip().upper()
            if request.status and request.status.strip()
            else None
        )
        offset = (
            request.page - 1
        ) * request.page_size

        items, total = await self._list_knowledge_spaces.execute(
            limit=request.page_size,
            offset=offset,
            enterprise_id=request.enterprise_id,
            search=search,
            status=status,
        )

        return ListKnowledgeSpacesResponse(
            items=[
                KnowledgeSpaceListItemResponse(
                    id=item.id,
                    enterprise_id=item.enterprise_id,
                    enterprise_name=item.enterprise_name,
                    name=item.name,
                    code=item.code,
                    description=item.description,
                    status=item.status,
                    created_at=item.created_at,
                )
                for item in items
            ],
            page=request.page,
            page_size=request.page_size,
            total=total,
        )

    async def get_knowledge_space(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceResponse | None:

        knowledge_space = await self._get_knowledge_space.execute(
            knowledge_space_id,
        )

        if knowledge_space is None:
            return None

        return self._to_response(
            knowledge_space,
        )

    async def get_data_hub_config(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceDataHubConfigResponse:

        await self._ensure_knowledge_space_exists(
            knowledge_space_id,
        )

        config = await self._get_data_hub_config.execute(
            knowledge_space_id,
        )

        return KnowledgeSpaceDataHubConfigResponse(
            configured=config is not None,
            data=(
                self._to_data_hub_response(config)
                if config is not None
                else None
            ),
        )

    async def get_embedding_config(
        self,
        knowledge_space_id: UUID,
    ) -> KnowledgeSpaceEmbeddingConfigEnvelopeResponse:

        await self._ensure_knowledge_space_exists(
            knowledge_space_id,
        )

        config = await self._get_embedding_config.execute(
            knowledge_space_id,
        )

        return KnowledgeSpaceEmbeddingConfigEnvelopeResponse(
            configured=config is not None,
            data=(
                self._to_embedding_response(config)
                if config is not None
                else None
            ),
        )

    async def save_data_hub_config(
        self,
        knowledge_space_id: UUID,
        request: SaveDataHubConfigRequest,
    ) -> KnowledgeSpaceDataHubResponse:

        await self._ensure_knowledge_space_exists(
            knowledge_space_id,
        )

        provider = (
            await self._data_hub_provider_repository.get_by_id(
                request.data_hub_provider_id,
            )
        )

        if provider is None:
            raise ValueError(
                "Data hub provider not found"
            )

        if not provider.enabled:
            raise ValueError(
                "Data hub provider is disabled"
            )

        try:
            config = await self._save_data_hub_config.execute(
                KnowledgeSpaceDataHub(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    data_hub_provider_id=(
                        request.data_hub_provider_id
                    ),
                    configuration=request.configuration,
                    enabled=request.enabled,
                    created_at=None,
                    updated_at=None,
                )
            )

            await self._session.commit()

        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError(
                "Unable to save data hub config"
            ) from exc

        return self._to_data_hub_response(
            config,
        )

    async def save_embedding_config(
        self,
        knowledge_space_id: UUID,
        request: SaveEmbeddingConfigRequest,
    ) -> KnowledgeSpaceEmbeddingConfigResponse:

        await self._ensure_knowledge_space_exists(
            knowledge_space_id,
        )

        embedding_model = (
            await self._embedding_model_repository.get_by_id(
                request.embedding_model_id,
            )
        )

        if embedding_model is None:
            raise ValueError(
                "Embedding model not found"
            )

        if not embedding_model.enabled:
            raise ValueError(
                "Embedding model is disabled"
            )

        try:
            config = await self._save_embedding_config.execute(
                KnowledgeSpaceEmbeddingConfig(
                    id=None,
                    knowledge_space_id=knowledge_space_id,
                    embedding_model_id=request.embedding_model_id,
                    configuration=request.configuration,
                    enabled=request.enabled,
                    created_at=None,
                    updated_at=None,
                )
            )

            await self._session.commit()

        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError(
                "Unable to save embedding config"
            ) from exc

        return self._to_embedding_response(
            config,
        )

    async def _ensure_knowledge_space_exists(
        self,
        knowledge_space_id: UUID,
    ) -> None:
        knowledge_space = await self._get_knowledge_space.execute(
            knowledge_space_id,
        )

        if knowledge_space is None:
            raise ValueError(
                "Knowledge space not found"
            )

    @staticmethod
    def _validate_code(
        code: str,
    ) -> None:
        if not code or not code.strip():
            raise ValueError(
                "Knowledge space code is required"
            )

    @staticmethod
    def _validate_name(
        name: str,
    ) -> None:
        if not name or not name.strip():
            raise ValueError(
                "Knowledge space name is required"
            )

    @staticmethod
    def _to_response(
        knowledge_space: KnowledgeSpace,
    ) -> KnowledgeSpaceResponse:
        if knowledge_space.id is None:
            raise ValueError(
                "Knowledge space id is required"
            )

        return KnowledgeSpaceResponse(
            id=knowledge_space.id,
            enterprise_id=knowledge_space.enterprise_id,
            name=knowledge_space.name,
            code=knowledge_space.code,
            description=knowledge_space.description,
            status=knowledge_space.status,
            configuration=knowledge_space.configuration,
            created_at=knowledge_space.created_at,
            updated_at=knowledge_space.updated_at,
        )

    @staticmethod
    def _to_data_hub_response(
        config: KnowledgeSpaceDataHub,
    ) -> KnowledgeSpaceDataHubResponse:
        if config.id is None:
            raise ValueError(
                "Data hub config id is required"
            )

        return KnowledgeSpaceDataHubResponse(
            id=config.id,
            knowledge_space_id=config.knowledge_space_id,
            data_hub_provider_id=config.data_hub_provider_id,
            configuration=config.configuration,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )

    @staticmethod
    def _to_embedding_response(
        config: KnowledgeSpaceEmbeddingConfig,
    ) -> KnowledgeSpaceEmbeddingConfigResponse:
        if config.id is None:
            raise ValueError(
                "Embedding config id is required"
            )

        return KnowledgeSpaceEmbeddingConfigResponse(
            id=config.id,
            knowledge_space_id=config.knowledge_space_id,
            embedding_model_id=config.embedding_model_id,
            configuration=config.configuration,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
