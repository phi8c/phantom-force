from module.ai.llm.domain.entities.ai_model import (
    AIModel,
)
from module.ai.llm.infrastructure.persistence.models.ai_model_model import (
    AIModelModel,
)


class AIModelMapper:

    @staticmethod
    def to_entity(
        model: AIModelModel,
    ) -> AIModel:

        return AIModel(
            id=model.id,
            provider_id=model.provider_id,
            code=model.code,
            display_name=model.display_name,
            model_type=model.model_type,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            supports_stream=model.supports_stream,
            supports_json=model.supports_json,
            supports_vision=model.supports_vision,
            supports_tools=model.supports_tools,
            description=model.description,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: AIModel,
    ) -> AIModelModel:

        return AIModelModel(
            id=entity.id,
            provider_id=entity.provider_id,
            code=entity.code,
            display_name=entity.display_name,
            model_type=entity.model_type,
            context_window=entity.context_window,
            max_output_tokens=entity.max_output_tokens,
            supports_stream=entity.supports_stream,
            supports_json=entity.supports_json,
            supports_vision=entity.supports_vision,
            supports_tools=entity.supports_tools,
            description=entity.description,
            is_enabled=entity.is_enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def merge_into_model(
        model: AIModelModel,
        entity: AIModel,
    ) -> None:

        model.provider_id = entity.provider_id
        model.code = entity.code
        model.display_name = entity.display_name
        model.model_type = entity.model_type
        model.context_window = entity.context_window
        model.max_output_tokens = entity.max_output_tokens
        model.supports_stream = entity.supports_stream
        model.supports_json = entity.supports_json
        model.supports_vision = entity.supports_vision
        model.supports_tools = entity.supports_tools
        model.description = entity.description
        model.is_enabled = entity.is_enabled
