from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.ai.domain.entities.ai_provider import (
    AIProvider,
)


@dataclass
class AIProviderDTO:

    id: UUID | None

    code: str

    name: str

    provider_type: str

    base_url: str | None

    api_version: str | None

    description: str | None

    is_enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

    @staticmethod
    def from_entity(
        entity: AIProvider,
    ) -> "AIProviderDTO":

        return AIProviderDTO(
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

    def to_entity(
        self,
    ) -> AIProvider:

        return AIProvider(
            id=self.id,
            code=self.code,
            name=self.name,
            provider_type=self.provider_type,
            base_url=self.base_url,
            api_version=self.api_version,
            description=self.description,
            is_enabled=self.is_enabled,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
