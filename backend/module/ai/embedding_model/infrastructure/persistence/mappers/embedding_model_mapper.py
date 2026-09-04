from module.ai.embedding_model.domain.entities.embedding_model import (
    EmbeddingModel,
)

from module.ai.embedding_model.infrastructure.persistence.models.embedding_model_model import (
    EmbeddingModelModel,
)


class EmbeddingModelMapper:

    @staticmethod
    def to_entity(
        model: EmbeddingModelModel,
    ) -> EmbeddingModel:

        return EmbeddingModel(
            id=model.id,
            code=model.code,
            name=model.name,
            provider=model.provider,
            dimension=model.dimension,
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=None,
            updated_at=None,
        )

    @staticmethod
    def to_model(
        entity: EmbeddingModel,
    ) -> EmbeddingModelModel:

        return EmbeddingModelModel(
            id=entity.id,
            code=entity.code,
            name=entity.name,
            provider=entity.provider,
            dimension=entity.dimension,
            configuration=entity.configuration,
            enabled=entity.enabled,
        )
