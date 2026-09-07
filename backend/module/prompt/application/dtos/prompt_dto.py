from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from module.prompt.domain.entities.prompt import (
    Prompt,
)


@dataclass
class PromptDTO:

    id: UUID | None

    code: str

    name: str | None

    description: str | None

    system_prompt: str

    configuration: dict

    enabled: bool

    created_at: datetime | None

    updated_at: datetime | None

    @staticmethod
    def from_entity(
        entity: Prompt,
    ) -> "PromptDTO":

        return PromptDTO(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            system_prompt=entity.system_prompt,
            configuration=entity.configuration,
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(
        self,
    ) -> Prompt:

        return Prompt(
            id=self.id,
            code=self.code,
            name=self.name,
            description=self.description,
            system_prompt=self.system_prompt,
            configuration=self.configuration,
            enabled=self.enabled,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
