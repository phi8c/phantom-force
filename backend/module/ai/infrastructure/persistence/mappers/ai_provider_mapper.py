from module.ai.domain.entities.ai_provider import (
    AIProvider,
)
from module.ai.infrastructure.persistence.models.ai_provider_model import (
    AIProviderModel,
)


class AIProviderMapper:

    @staticmethod
    def to_entity(
        model: AIProviderModel,
    ) -> AIProvider:

        return AIProvider(
            id=model.id,
            code=model.code,
            name=model.name,
            provider_type=model.provider_type,
            base_url=model.base_url,
            api_version=model.api_version,
            description=model.description,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: AIProvider,
    ) -> AIProviderModel:

        return AIProviderModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            provider_type=entity.provider_type,
            base_url=entity.base_url,
            api_version=entity.api_version,
            description=entity.description,
            is_enabled=entity.is_enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def merge_into_model(
        model: AIProviderModel,
        entity: AIProvider,
    ) -> None:

        model.code = entity.code
        model.name = entity.name
        model.provider_type = entity.provider_type
        model.base_url = entity.base_url
        model.api_version = entity.api_version
        model.description = entity.description
        model.is_enabled = entity.is_enabled
