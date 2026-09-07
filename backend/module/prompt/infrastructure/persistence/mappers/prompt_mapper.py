from module.prompt.domain.entities.prompt import (
    Prompt,
)
from module.prompt.infrastructure.persistence.models.prompt_model import (
    PromptModel,
)


class PromptMapper:

    @staticmethod
    def to_entity(
        model: PromptModel,
    ) -> Prompt:

        return Prompt(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            system_prompt=model.system_prompt,
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: Prompt,
    ) -> PromptModel:

        return PromptModel(
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

    @staticmethod
    def merge_into_model(
        model: PromptModel,
        entity: Prompt,
    ) -> None:

        model.code = entity.code
        model.name = entity.name
        model.description = entity.description
        model.system_prompt = entity.system_prompt
        model.configuration = entity.configuration
        model.enabled = entity.enabled
