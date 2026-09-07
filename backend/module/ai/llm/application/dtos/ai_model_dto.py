from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.ai.llm.domain.entities.ai_model import (
    AIModel,
)


@dataclass
class AIModelDTO:

    id: UUID | None

    provider_id: UUID

    code: str

    display_name: str

    model_type: str

    context_window: int | None

    max_output_tokens: int | None

    supports_stream: bool

    supports_json: bool

    supports_vision: bool

    supports_tools: bool

    description: str | None

    is_enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

    @staticmethod
    def from_entity(
        entity: AIModel,
    ) -> "AIModelDTO":

        return AIModelDTO(
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

    def to_entity(
        self,
    ) -> AIModel:

        return AIModel(
            id=self.id,
            provider_id=self.provider_id,
            code=self.code,
            display_name=self.display_name,
            model_type=self.model_type,
            context_window=self.context_window,
            max_output_tokens=self.max_output_tokens,
            supports_stream=self.supports_stream,
            supports_json=self.supports_json,
            supports_vision=self.supports_vision,
            supports_tools=self.supports_tools,
            description=self.description,
            is_enabled=self.is_enabled,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
