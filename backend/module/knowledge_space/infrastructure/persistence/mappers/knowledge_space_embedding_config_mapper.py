from module.knowledge_space.domain.entities.knowledge_space_embedding_config import (
    KnowledgeSpaceEmbeddingConfig,
)

from module.knowledge_space.infrastructure.persistence.models.knowledge_space_embedding_config_model import (
    KnowledgeSpaceEmbeddingConfigModel,
)


class KnowledgeSpaceEmbeddingConfigMapper:

    @staticmethod
    def to_entity(
        model: KnowledgeSpaceEmbeddingConfigModel,
    ) -> KnowledgeSpaceEmbeddingConfig:

        return KnowledgeSpaceEmbeddingConfig(
            id=model.id,
            knowledge_space_id=(
                model.knowledge_space_id
            ),
            embedding_model_id=(
                model.embedding_model_id
            ),
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: KnowledgeSpaceEmbeddingConfig,
    ) -> KnowledgeSpaceEmbeddingConfigModel:

        return KnowledgeSpaceEmbeddingConfigModel(
            id=entity.id,
            knowledge_space_id=(
                entity.knowledge_space_id
            ),
            embedding_model_id=(
                entity.embedding_model_id
            ),
            configuration=entity.configuration,
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )