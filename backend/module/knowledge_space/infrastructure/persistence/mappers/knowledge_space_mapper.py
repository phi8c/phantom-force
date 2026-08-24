from module.knowledge_space.domain.entities.knowledge_space import (
    KnowledgeSpace,
)

from module.knowledge_space.infrastructure.persistence.models.knowledge_space_model import (
    KnowledgeSpaceModel,
)


class KnowledgeSpaceMapper:

    @staticmethod
    def to_entity(
        model: KnowledgeSpaceModel,
    ) -> KnowledgeSpace:

        return KnowledgeSpace(
            id=model.id,
            enterprise_id=model.enterprise_id,
            name=model.name,
            code=model.code,
            description=model.description,
            status=model.status,
            configuration=model.configuration,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(
        entity: KnowledgeSpace,
    ) -> KnowledgeSpaceModel:

        return KnowledgeSpaceModel(
            id=entity.id,
            enterprise_id=entity.enterprise_id,
            name=entity.name,
            code=entity.code,
            description=entity.description,
            status=entity.status,
            configuration=entity.configuration,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )