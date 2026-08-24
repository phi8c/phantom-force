from module.knowledge_space.domain.entities.knowledge_space_data_hub import (
    KnowledgeSpaceDataHub,
)

from module.knowledge_space.infrastructure.persistence.models.knowledge_space_data_hub_model import (
    KnowledgeSpaceDataHubModel,
)


class KnowledgeSpaceDataHubMapper:

    @staticmethod
    def to_entity(
        model: KnowledgeSpaceDataHubModel,
    ) -> KnowledgeSpaceDataHub:

        return KnowledgeSpaceDataHub(
            id=model.id,
            knowledge_space_id=model.knowledge_space_id,
            data_hub_provider_id=(
                model.data_hub_provider_id
            ),
            configuration=model.configuration,
            enabled=model.enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: KnowledgeSpaceDataHub,
    ) -> KnowledgeSpaceDataHubModel:

        return KnowledgeSpaceDataHubModel(
            id=entity.id,
            knowledge_space_id=(
                entity.knowledge_space_id
            ),
            data_hub_provider_id=(
                entity.data_hub_provider_id
            ),
            configuration=entity.configuration,
            enabled=entity.enabled,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )